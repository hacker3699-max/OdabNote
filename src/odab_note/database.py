import sqlite3
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

DEFAULT_DB_PATH = os.path.expanduser("~/.gemini/antigravity/odab_note.db")

class OdabNoteDB:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._get_connection() as conn:
            # 1. 오답노트 테이블 (last_occurred_at, decay_factor, target_model 속성 기본 포함)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incorrect_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    error_pattern TEXT NOT NULL,
                    solution TEXT NOT NULL,
                    occurrence_count INTEGER DEFAULT 1,
                    is_verified BOOLEAN DEFAULT 0,
                    last_occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    decay_factor REAL DEFAULT 0.1,
                    target_model TEXT DEFAULT 'all'
                )
            """)
            # 2. 세션 메모리 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 3. 에이전트 스킬 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    cmd TEXT NOT NULL,
                    desc TEXT NOT NULL,
                    is_verified BOOLEAN DEFAULT 0
                )
            """)
            # 4. 오답 노드 간의 관계 및 상충(Conflict) 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incorrect_note_relations (
                    from_note_id INTEGER,
                    to_note_id INTEGER,
                    relation_type TEXT NOT NULL, -- 'conflict', 'triggers', 'parent_of'
                    PRIMARY KEY (from_note_id, to_note_id),
                    FOREIGN KEY (from_note_id) REFERENCES incorrect_notes(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_note_id) REFERENCES incorrect_notes(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

        # 스키마 마이그레이션 (기존 생성 테이블용 하위 호환성 패치)
        with self._get_connection() as conn:
            try:
                conn.execute("ALTER TABLE incorrect_notes ADD COLUMN last_occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE incorrect_notes ADD COLUMN decay_factor REAL DEFAULT 0.1")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE incorrect_notes ADD COLUMN target_model TEXT DEFAULT 'all'")
            except sqlite3.OperationalError:
                pass
            conn.commit()

    # --- incorrect_notes CRUD ---
    def add_mistake(self, keyword: str, error_pattern: str, solution: str, target_model: str = 'all', is_verified: bool = False) -> int:
        with self._get_connection() as conn:
            # 기존에 동일한 keyword와 error_pattern, target_model이 있는지 확인하여 카운트 증가
            cursor = conn.execute("""
                SELECT id, occurrence_count FROM incorrect_notes 
                WHERE keyword = ? AND error_pattern = ? AND target_model = ?
            """, (keyword, error_pattern, target_model))
            row = cursor.fetchone()
            if row:
                note_id = row["id"]
                conn.execute("""
                    UPDATE incorrect_notes 
                    SET occurrence_count = occurrence_count + 1, solution = ?, last_occurred_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (solution, note_id))
                conn.commit()
                return note_id
            else:
                cursor = conn.execute("""
                    INSERT INTO incorrect_notes (keyword, error_pattern, solution, is_verified, last_occurred_at, decay_factor, target_model) 
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 0.1, ?)
                """, (keyword, error_pattern, solution, 1 if is_verified else 0, target_model))
                conn.commit()
                return cursor.lastrowid

    def query_notes(self, keywords: List[str], only_verified: bool = False) -> List[Dict[str, Any]]:
        if not keywords:
            return []
        
        # 키워드 매칭 쿼리 (OR 조건)
        query = "SELECT * FROM incorrect_notes WHERE (" + " OR ".join(["keyword LIKE ?" for _ in keywords]) + ")"
        params = [f"%{k}%" for k in keywords]
        
        if only_verified:
            query += " AND is_verified = 1"
            
        query += " ORDER BY occurrence_count DESC"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            notes = [dict(row) for row in cursor.fetchall()]
            
            # 각 오답노트의 2차 연관 및 상충 오답들도 가져와 주입
            for note in notes:
                note['conflicts'] = self.get_related_notes_by_type(note['id'], 'conflict')
                note['relations'] = self.get_related_notes_by_type(note['id'], 'triggers')
            return notes

    def match_error_trace(self, error_trace: str, target_model: str = 'all', only_verified: bool = False) -> List[Dict[str, Any]]:
        """Match error trace against wrong-answer note regex patterns and retrieve matches."""
        notes = self.list_all_notes()
        matched_notes = []
        for note in notes:
            if only_verified and not note['is_verified']:
                continue
            
            # target_model 필터링 (all이거나 혹은 요청한 모델명과 매칭될 때만)
            note_model = note.get('target_model', 'all')
            if target_model != 'all' and note_model != 'all' and note_model != target_model:
                continue

            try:
                # 정규식 대소문자 구분 없이, 줄바꿈도 매치하도록 컴파일
                pattern = re.compile(note['error_pattern'], re.IGNORECASE | re.DOTALL)
                if pattern.search(error_trace):
                    note_id = note['id']
                    note['conflicts'] = self.get_related_notes_by_type(note_id, 'conflict')
                    note['relations'] = self.get_related_notes_by_type(note_id, 'triggers')
                    
                    # 매치된 에러이므로 최신 시간 갱신 (감쇠 방지)
                    with self._get_connection() as conn:
                        conn.execute("UPDATE incorrect_notes SET last_occurred_at = CURRENT_TIMESTAMP WHERE id = ?", (note_id,))
                        conn.commit()
                        
                    matched_notes.append(note)
            except re.error:
                # 패턴 오류 시 단순 텍스트 서브스트링 비교 폴백
                if note['error_pattern'].lower() in error_trace.lower():
                    note_id = note['id']
                    note['conflicts'] = self.get_related_notes_by_type(note_id, 'conflict')
                    note['relations'] = self.get_related_notes_by_type(note_id, 'triggers')
                    matched_notes.append(note)
                    
        # 가중치 우선 내림차순 정렬하되, target_model이 정확히 일치하는 것을 최우선 정렬 보너스 부여
        def sort_key(x):
            model_bonus = 1000 if x.get('target_model') == target_model and target_model != 'all' else 0
            return x['occurrence_count'] + model_bonus

        matched_notes.sort(key=sort_key, reverse=True)
        return matched_notes

    def apply_decay(self, days_threshold: int = 7) -> int:
        """Decrease occurrence_count of notes not triggered for days_threshold days."""
        with self._get_connection() as conn:
            # last_occurred_at이 days_threshold보다 과거인 항목들 가중치 차감 (최소 1)
            cursor = conn.execute("""
                UPDATE incorrect_notes 
                SET occurrence_count = MAX(1, CAST(occurrence_count * (1.0 - decay_factor) AS INTEGER))
                WHERE last_occurred_at < datetime('now', ?) AND occurrence_count > 1
            """, (f"-{days_threshold} days",))
            conn.commit()
            return cursor.rowcount

    def update_verification(self, note_id: int, is_verified: bool) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE incorrect_notes SET is_verified = ? WHERE id = ?",
                (1 if is_verified else 0, note_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_note(self, note_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM incorrect_notes WHERE id = ?", (note_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_all_notes(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM incorrect_notes ORDER BY occurrence_count DESC")
            return [dict(row) for row in cursor.fetchall()]

    # --- Relations and Conflict Handling ---
    def add_relation(self, from_id: int, to_id: int, relation_type: str = 'conflict'):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO incorrect_note_relations (from_note_id, to_note_id, relation_type) VALUES (?, ?, ?)",
                (from_id, to_id, relation_type)
            )
            if relation_type == 'conflict':
                # 상충 관계는 양방향으로 등록
                conn.execute(
                    "INSERT OR IGNORE INTO incorrect_note_relations (from_note_id, to_note_id, relation_type) VALUES (?, ?, ?)",
                    (to_id, from_id, relation_type)
                )
            conn.commit()

    def get_related_notes_by_type(self, note_id: int, relation_type: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT n.* FROM incorrect_notes n
                JOIN incorrect_note_relations r ON n.id = r.to_note_id
                WHERE r.from_note_id = ? AND r.relation_type = ?
            """, (note_id, relation_type))
            return [dict(row) for row in cursor.fetchall()]

    def merge_and_replace_notes(self, keep_id: int, delete_id: int, merged_solution: str, merged_keyword: str) -> bool:
        """Merge two conflicting notes into one, update the solution, and delete the other."""
        with self._get_connection() as conn:
            # 1. 유지할 노트의 솔루션, 키워드, 카운트 갱신
            cursor = conn.execute("SELECT occurrence_count FROM incorrect_notes WHERE id = ?", (delete_id,))
            del_row = cursor.fetchone()
            del_count = del_row["occurrence_count"] if del_row else 1
            
            conn.execute("""
                UPDATE incorrect_notes 
                SET solution = ?, keyword = ?, occurrence_count = occurrence_count + ?, is_verified = 1, last_occurred_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (merged_solution, merged_keyword, del_count, keep_id))
            
            # 2. 다른 노트 삭제
            conn.execute("DELETE FROM incorrect_notes WHERE id = ?", (delete_id,))
            
            # 3. 구 관계 정보 클린업 및 업데이트
            conn.execute("DELETE FROM incorrect_note_relations WHERE from_note_id = ? OR to_note_id = ?", (delete_id, delete_id))
            conn.commit()
            return True


    # --- agent_skills CRUD ---
    def register_skill(self, name: str, cmd: str, desc: str, is_verified: bool = False) -> bool:
        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO agent_skills (name, cmd, desc, is_verified) VALUES (?, ?, ?, ?)",
                    (name, cmd, desc, 1 if is_verified else 0)
                )
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    def list_skills(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM agent_skills")
            return [dict(row) for row in cursor.fetchall()]
