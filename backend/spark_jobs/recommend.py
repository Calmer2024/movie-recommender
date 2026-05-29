"""
Spark ALS 协同过滤推荐算法
从 GaussDB 读取评分数据 → 训练 ALS 模型 → 预测评分 → 写回数据库
"""
import os
import sys

# Windows 上 PySpark 需要设置 PYSPARK_PYTHON
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.sql.types import IntegerType, FloatType, StructType, StructField
from pyspark.sql.functions import explode, col, lit, current_timestamp


DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'dbname': 'movie_db',
    'user': 'gaussdb',
    'password': 'gaussdb123'
}


def get_spark_session():
    """创建 Spark 会话"""
    return SparkSession.builder \
        .appName("MovieRecommender") \
        .master("local[*]") \
        .getOrCreate()


def load_ratings_from_db(spark):
    """从数据库加载评分数据"""
    import psycopg

    conn = psycopg.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        dbname=DB_CONFIG['dbname'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    cur = conn.cursor()
    cur.execute("SELECT user_id, movie_id, score FROM ratings")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    print(f"  从数据库加载了 {len(rows)} 条评分记录")

    # 创建 Spark DataFrame
    schema = StructType([
        StructField("user_id", IntegerType(), True),
        StructField("movie_id", IntegerType(), True),
        StructField("score", FloatType(), True),
    ])
    return spark.createDataFrame(rows, schema=schema)


def save_recommendations_to_db(recommendations):
    """将推荐结果写回数据库"""
    import psycopg

    conn = psycopg.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        dbname=DB_CONFIG['dbname'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    cur = conn.cursor()

    # 清除旧的 ALS 推荐
    cur.execute("DELETE FROM recommendations WHERE algorithm = 'als'")

    # 写入新推荐
    insert_sql = "INSERT INTO recommendations (user_id, movie_id, score, algorithm) VALUES (%s, %s, %s, 'als')"
    cur.executemany(insert_sql, recommendations)
    conn.commit()

    cur.close()
    conn.close()


def main():
    print("=" * 50)
    print("开始 Spark ALS 推荐计算...")
    print("=" * 50)

    spark = get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    # 1. 加载数据
    print("[1/4] 从数据库加载评分数据...")
    ratings_df = load_ratings_from_db(spark)
    count = ratings_df.count()
    print(f"  共 {count} 条评分记录")

    if count < 10:
        print("  评分数据不足（<10条），跳过推荐计算")
        spark.stop()
        return

    # 2. 训练 ALS 模型
    print("[2/4] 训练 ALS 协同过滤模型...")
    als = ALS(
        maxIter=10,
        regParam=0.1,
        rank=10,
        userCol="user_id",
        itemCol="movie_id",
        ratingCol="score",
        coldStartStrategy="drop",
        nonnegative=True
    )
    model = als.fit(ratings_df)
    print("  模型训练完成")

    # 3. 为所有用户生成 Top 10 推荐
    print("[3/4] 生成用户推荐列表...")
    user_recs = model.recommendForAllUsers(10)

    # 展平推荐结果
    recs_flat = user_recs.select(
        col("user_id"),
        explode(col("recommendations")).alias("rec")
    ).select(
        col("user_id"),
        col("rec.movie_id").alias("movie_id"),
        col("rec.rating").alias("score")
    )

    # 转为 Python 列表
    recs_list = recs_flat.collect()
    recommendations = [(r.user_id, r.movie_id, float(r.score)) for r in recs_list]
    print(f"  生成了 {len(recommendations)} 条推荐记录")

    # 4. 写回数据库
    print("[4/4] 将推荐结果写入数据库...")
    save_recommendations_to_db(recommendations)
    print(f"  写入完成")

    print("=" * 50)
    print("推荐计算完成！")
    print("=" * 50)

    spark.stop()


if __name__ == '__main__':
    main()
