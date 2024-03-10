from neo4j import GraphDatabase
import pandas as pd

uri = "neo4j://localhost:7687/"
driver = GraphDatabase.driver(uri, auth=("neo4j", "ntCcYttVSsB1kIIYNC8cn66th5OR1y1lXXOgP38oDKI"))

k = 10  # nearest neighbors (most similar users) to consider
m_common = 3  # how many titles in common to be consider an user similar
users_common = 2  # minimum number of similar users that have seen the title to consider it
threshold_sim = 0 # threshold to consider users similar


def load_data():
    with driver.session() as session:
        session.run("""MATCH ()-[r]->() DELETE r""")
        session.run("""MATCH (r) DELETE r""")

        print("Loading chapter...")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///out_Genre.csv" AS csv
            CREATE (:Genre {genre: csv.genre})
            """)

        print("Loading section...")
        session.run("""
	    LOAD CSV WITH HEADERS FROM "file:///out_genre_section.csv" AS csv
            CREATE (:Title {title: csv.section})
            """)
        print("Loading content...")
        session.run("""
             LOAD CSV WITH HEADERS FROM "file:///out_section_content.csv" AS csv
             CREATE (:Content {content: csv.content})
                    """)
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///out_genre_section.csv" AS csv
            MERGE (m:Genre {genre: csv.genre})
            MERGE (p:Title{title: csv.section})
            CREATE (m)-[:章节包含]->(p)
            """)
        session.run("""
	        LOAD CSV WITH HEADERS FROM "file:///out_section_content.csv" AS csv
            MERGE (m:Title {title: csv.section})
            MERGE (k:Content{content: csv.content})
            CREATE (m)-[:知识点包含]->(k)   
            """)
        print("Loading users...")
        session.run("""
            LOAD CSV WITH HEADERS FROM "file:///out_grade.csv" AS csv
            MERGE (p:Title {title: csv.section})
            MERGE (u:Users {id: toInteger(csv.id)})
            CREATE (u)-[:评分 {grading : toInteger(csv.grade)}]->(p)
            """)

def queries():
    while True:
        userid = int(input("请输入用户名，以查询用户喜欢列表: "))
        m = int(input("为该用户推荐多少个呢？ "))

        genres = []
        if int(input("是否需要过滤掉不喜欢的类型?（输入0或1）")):  # 过滤掉不喜欢的章节
            with driver.session() as session:
                try:
                    q = session.run(f"""MATCH (g:Genre) RETURN g.genre AS genre""")
                    result = []
                    for i, r in enumerate(q):
                        result.append(r["genre"])  # 找到图谱中所有的知识点类型
                    df = pd.DataFrame(result, columns=["genre"])
                    print()
                    print(df)
                    inp = input("输入不喜欢的类型索引即可，例如：1 2 3  ")
                    if len(inp) != 0:
                        inp = inp.split(" ")
                        genres = [df["genre"].iloc[int(x)] for x in inp]
                except:
                    print("Error")

        with driver.session() as session:  # 找到当前ID评分的知识点
            q = session.run(f"""
                    MATCH (u1:Users {{id : {userid}}})-[r:评分]-(m:Title)
                    RETURN m.title AS session, r.grading AS grade
                    ORDER BY grade DESC
                    """)

            print()
            print("Your ratings are the following:")

            result = []
            for r in q:
                result.append([r["session"], r["grade"]])

            if len(result) == 0:
                print("No ratings found")
            else:
                df = pd.DataFrame(result, columns=["session", "grade"])
                print()
                print(df.to_string(index=False))
            print()

            session.run(f"""
                MATCH (u1:Users)-[s:相似之处]-(u2:Users)
                DELETE s
                """)
            # 找到当前用户评分的知识点以及这些知识点被其他用户评分的用户，with是把查询集合当做结果以便后面用where 余弦相似度计算
            session.run(f"""
                MATCH (u1:Users {{id : {userid}}})-[r1:评分]-(m:Title)-[r2:评分]-(u2:Users)
                WITH
                    u1, u2,
                    COUNT(m) AS session_common,
                    SUM(r1.grading * r2.grading)/(SQRT(SUM(r1.grading^2)) * SQRT(SUM(r2.grading^2))) AS sim
                WHERE session_common >= {m_common} AND sim > {threshold_sim}
                MERGE (u1)-[s:相似之处]-(u2)
                SET s.sim = sim
                """)

            Q_GENRE = ""
            if (len(genres) > 0):
                Q_GENRE = "AND ((SIZE(gen) > 0) AND "
                Q_GENRE += "(ANY(x IN " + str(genres) + " WHERE x IN gen))"
                Q_GENRE += ")"
            # 找到相似的用户，然后看他们喜欢什么类型知识点 Collect：将所有值收集到一个集合list中
            q = session.run(f"""
                    MATCH (u1:Users {{id : {userid}}})-[s:相似之处]-(u2:Users)
                    WITH u1, u2, s
                    ORDER BY s.sim DESC LIMIT {k}
                    MATCH (m:Title)-[r:评分]-(u2)
                    OPTIONAL MATCH (g:Genre)--(m)
                    WITH u1, u2, s, m, r, COLLECT(DISTINCT g.genre) AS gen
                    WHERE NOT((m)-[:RATED]-(u1)) {Q_GENRE}
                    WITH
                        m.title AS title,
                        SUM(r.grading * s.sim)/SUM(s.sim) AS grade,
                        COUNT(u2) AS num,
                        gen
                    WHERE num >= {users_common}
                    RETURN title, grade, num, gen
                    ORDER BY grade DESC, num DESC
                    LIMIT {m}
                    """)

            print("Recommended session:")

            result = []
            for r in q:
                result.append([r["title"], r["grade"], r["num"], r["gen"]])
            if len(result) == 0:
                print("No recommendations found")
                print()
                continue
            df = pd.DataFrame(result, columns=["title", "avg grade", "num recommenders", "genres"])
            print()
            print(df.to_string(index=False))
            print()


if __name__ == "__main__":
    if int(input("是否需要重新加载并创建知识图谱？（请选择输入0或1）")):
        load_data()
    queries()