"""
事件关系图 - 基于 Neo4j 的时间视角
"""
from neo4j import GraphDatabase
from datetime import datetime
import os


class EventGraph:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password=None):
        password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_event(self, event_id: int, summary: str, emotion: str, timestamp: str, topic: str = None):
        """添加事件节点"""
        with self.driver.session() as session:
            session.run(
                """
                CREATE (e:Event {
                    id: $id,
                    summary: $summary,
                    emotion: $emotion,
                    timestamp: $timestamp,
                    topic: $topic
                })
                """,
                id=event_id, summary=summary, emotion=emotion,
                timestamp=timestamp, topic=topic
            )

    def link_events(self, from_id: int, to_id: int, relation: str = "LEADS_TO"):
        """连接两个事件（因果关系）"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (a:Event {id: $from_id})
                MATCH (b:Event {id: $to_id})
                CREATE (a)-[r:RELATION {type: $relation}]->(b)
                """,
                from_id=from_id, to_id=to_id, relation=relation
            )

    def get_event_chain(self, topic: str, limit: int = 10):
        """获取某个话题的事件链"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Event {topic: $topic})
                RETURN e.id as id, e.summary as summary, e.timestamp as timestamp
                ORDER BY e.timestamp DESC
                LIMIT $limit
                """,
                topic=topic, limit=limit
            )
            return [dict(record) for record in result]
