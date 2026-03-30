"""
图数据库模块 - Neo4j 事件关系图

存储结构：
- (User) 节点
- (Event) 节点：重要事件，带时间戳和情绪
- (Memory) 节点：对话记忆
- (Emotion) 节点：情绪状态
- CAUSED 关系：事件A 导致 事件B
- RELATED 关系：事件相关联
- FELT 关系：用户在某事件中感受到某情绪
- MENTIONED 关系：用户多次提到某话题
"""
from neo4j import GraphDatabase
from datetime import datetime
from typing import List, Dict, Optional


class EventGraph:
    """Neo4j 事件关系图"""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="xiaolu2024"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._init_schema()

    def close(self):
        self.driver.close()

    def _init_schema(self):
        """初始化图数据库结构"""
        with self.driver.session() as session:
            session.run("""
                CREATE CONSTRAINT user_uid IF NOT EXISTS
                FOR (u:User) REQUIRE u.uid IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT event_eid IF NOT EXISTS
                FOR (e:Event) REQUIRE e.eid IS UNIQUE
            """)

    # ─── 1. 创建节点 ──────────────────────────────────────

    def create_user(self, user_id: str, nickname: str = "新朋友"):
        """创建用户节点"""
        with self.driver.session() as session:
            session.run("""
                MERGE (u:User {uid: $uid})
                SET u.nickname = $nickname,
                    u.created_at = $now,
                    u.last_seen = $now
            """, uid=user_id, nickname=nickname, now=datetime.now().isoformat())

    def add_event(self, user_id: str, event_id: str, summary: str,
                  emotion: str = "", importance: int = 5,
                  timestamp: str = None):
        """添加事件节点"""
        if not timestamp:
            timestamp = datetime.now().isoformat()

        with self.driver.session() as session:
            session.run("""
                MATCH (u:User {uid: $uid})
                CREATE (e:Event {
                    eid: $eid,
                    summary: $summary,
                    emotion: $emotion,
                    importance: $importance,
                    created_at: $timestamp
                })
                CREATE (u)-[:EXPERIENCED]->(e)
            """, uid=user_id, eid=event_id, summary=summary,
                 emotion=emotion, importance=importance, timestamp=timestamp)

    def add_conversation(self, user_id: str, conv_id: str,
                         user_input: str, ai_response: str):
        """添加对话记忆节点"""
        with self.driver.session() as session:
            session.run("""
                MATCH (u:User {uid: $uid})
                CREATE (m:Memory {
                    mid: $mid,
                    user_input: $user_input,
                    ai_response: $ai_response,
                    created_at: $timestamp
                })
                CREATE (u)-[:SAID]->(m)
            """, uid=user_id, mid=conv_id, user_input=user_input,
                 ai_response=ai_response, timestamp=datetime.now().isoformat())

    # ─── 2. 创建关系 ──────────────────────────────────────

    def link_events(self, event_id_a: str, event_id_b: str,
                    relation: str = "RELATED", label: str = ""):
        """连接两个事件"""
        with self.driver.session() as session:
            if relation == "CAUSED":
                session.run("""
                    MATCH (a:Event {eid: $ida}), (b:Event {eid: $idb})
                    MERGE (a)-[r:CAUSED {label: $label}]->(b)
                """, ida=event_id_a, idb=event_id_b, label=label)
            else:
                session.run("""
                    MATCH (a:Event {eid: $ida}), (b:Event {eid: $idb})
                    MERGE (a)-[r:RELATED {label: $label}]->(b)
                """, ida=event_id_a, idb=event_id_b, label=label)

    def link_event_to_emotion(self, event_id: str, emotion: str):
        """连接事件和情绪"""
        with self.driver.session() as session:
            session.run("""
                MATCH (e:Event {eid: $eid})
                MERGE (em:Emotion {name: $emotion})
                MERGE (e)-[:FELT]->(em)
            """, eid=event_id, emotion=emotion)

    def link_conversation_to_event(self, conv_id: str, event_id: str):
        """连接对话和事件"""
        with self.driver.session() as session:
            session.run("""
                MATCH (m:Memory {mid: $mid}), (e:Event {eid: $eid})
                MERGE (m)-[:ABOUT]->(e)
            """, mid=conv_id, eid=event_id)

    def link_topic_mentions(self, event_id: str, topic: str):
        """记录话题被多次提到"""
        with self.driver.session() as session:
            session.run("""
                MATCH (e:Event {eid: $eid})
                MERGE (t:Topic {name: $topic})
                MERGE (e)-[:ABOUT_TOPIC]->(t)
                ON CREATE SET t.mention_count = 1
                ON MATCH SET t.mention_count = t.mention_count + 1
            """, eid=event_id, topic=topic)

    # ─── 3. 查询：时间视角 ────────────────────────────────

    def get_events_by_period(self, user_id: str, days: int = 30) -> List[Dict]:
        """获取某段时间内的事件"""
        cutoff = (datetime.now() - __import__('datetime').timedelta(days=days)).isoformat()
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {uid: $uid})-[:EXPERIENCED]->(e:Event)
                WHERE e.created_at > $cutoff
                RETURN e.eid AS eid, e.summary AS summary, 
                       e.emotion AS emotion, e.created_at AS time,
                       e.importance AS importance
                ORDER BY e.created_at DESC
            """, uid=user_id, cutoff=cutoff)
            return [dict(record) for record in result]

    def get_event_chain(self, user_id: str, event_id: str) -> List[Dict]:
        """获取事件的因果链：A→B→C"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {uid: $uid})-[:EXPERIENCED]->(start:Event {eid: $eid})
                OPTIONAL MATCH path = (start)-[:CAUSED|RELATED*1..5]->(end:Event)
                UNWIND nodes(path) AS node
                WITH DISTINCT node
                RETURN node.summary AS summary, node.created_at AS time,
                       node.emotion AS emotion
                ORDER BY node.created_at
            """, uid=user_id, eid=event_id)
            return [dict(record) for record in result]

    def query_past_feeling(self, user_id: str, query: str, months: int = 3) -> str:
        """查询'N个月前在纠结什么'"""
        cutoff = (datetime.now() - __import__('datetime').timedelta(days=months*30)).isoformat()
        end = (datetime.now() - __import__('datetime').timedelta(days=(months-1)*30)).isoformat()

        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {uid: $uid})-[:EXPERIENCED]->(e:Event)
                WHERE e.created_at > $cutoff AND e.created_at < $end
                RETURN e.summary AS summary, e.emotion AS emotion, 
                       e.created_at AS time, e.importance AS importance
                ORDER BY e.importance DESC
                LIMIT 5
            """, uid=user_id, cutoff=cutoff, end=end)
            events = [dict(r) for r in result]

        if not events:
            return f"{months}个月前没有记录到重要事件呢"

        lines = [f"🗓️ {months}个月前你在关注这些事：\n"]
        for e in events:
            date = e['time'][:10]
            lines.append(f"• {date} [{e.get('emotion','')}] {e['summary']}")
        
        return "\n".join(lines)

    def get_topic_trend(self, user_id: str, topic: str) -> List[Dict]:
        """获取话题的时间趋势（情绪变化）"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {uid: $uid})-[:EXPERIENCED]->(e:Event)
                       -[:ABOUT_TOPIC]->(t:Topic {name: $topic})
                RETURN e.summary AS summary, e.emotion AS emotion,
                       e.created_at AS time
                ORDER BY e.created_at ASC
            """, uid=user_id, topic=topic)
            return [dict(record) for record in result]

    def get_most_discussed_topics(self, user_id: str, limit: int = 5) -> List[Dict]:
        """获取用户讨论最多的话题"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {uid: $uid})-[:EXPERIENCED]->(e:Event)
                       -[:ABOUT_TOPIC]->(t:Topic)
                RETURN t.name AS topic, t.mention_count AS count
                ORDER BY count DESC LIMIT $limit
            """, uid=user_id, limit=limit)
            return [dict(record) for record in result]

    # ─── 4. 变化识别 ──────────────────────────────────────

    def detect_emotion_shift(self, user_id: str) -> Optional[Dict]:
        """检测用户情绪变化（对比不同时间段）"""
        from datetime import timedelta
        recent_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        older_cutoff = (datetime.now() - timedelta(days=30)).isoformat()

        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {uid: $uid})-[:EXPERIENCED]->(e:Event)-[:FELT]->(em:Emotion)
                WHERE e.created_at > $older_cutoff
                WITH em.name AS emotion, 
                     CASE WHEN e.created_at > $recent_cutoff THEN 'recent' ELSE 'older' END AS period,
                     count(*) AS cnt
                RETURN emotion, period, cnt
            """, uid=user_id, recent_cutoff=recent_cutoff, older_cutoff=older_cutoff)
            data = [dict(r) for r in result]

        if not data:
            return None

        recent = {d['emotion']: d['cnt'] for d in data if d['period'] == 'recent'}
        older = {d['emotion']: d['cnt'] for d in data if d['period'] == 'older'}

        # 找到情绪变化
        all_emotions = set(list(recent.keys()) + list(older.keys()))
        shifts = []
        for em in all_emotions:
            old_count = older.get(em, 0)
            new_count = recent.get(em, 0)
            if old_count != new_count:
                shifts.append({
                    'emotion': em,
                    'before': old_count,
                    'after': new_count,
                    'direction': 'increased' if new_count > old_count else 'decreased'
                })

        return {'shifts': shifts} if shifts else None
