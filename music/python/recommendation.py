import pandas as pd
import numpy as np

# 读取CSV文件
ratings = pd.read_csv('ratings.csv')

# 假设有100位用户对86个章节的评分，构建一个用户-章节评分矩阵
num_users = ratings['userId'].nunique()
num_sections = ratings['sectionId'].nunique()

# 创建用户-章节评分矩阵
ratings_matrix = np.zeros((num_users, num_sections))

# 将评分数据填入矩阵中
for index, row in ratings.iterrows():
    user_id = row['userId']
    section_id = row['sectionId']
    rating = row['rating']
    ratings_matrix[user_id - 1][section_id - 1] = rating  # 注意用户ID和章节ID从1开始，所以要减1

# 计算用户之间的相似度，这里使用余弦相似度
def cosine_similarity(user1_ratings, user2_ratings):
    dot_product = np.dot(user1_ratings, user2_ratings)
    norm_user1 = np.linalg.norm(user1_ratings)
    norm_user2 = np.linalg.norm(user2_ratings)
    return dot_product / (norm_user1 * norm_user2)

# 基于用户的协同过滤算法
def user_based_collaborative_filtering(target_user_index, ratings, num_recommendations=10):
    similarities = []
    target_user_ratings = ratings[target_user_index]

    # 计算目标用户与其他用户的相似度
    for i in range(len(ratings)):
        if i != target_user_index:
            similarity = cosine_similarity(target_user_ratings, ratings[i])
            similarities.append((i, similarity))

    # 确保相似用户列表中有足够的元素
    if len(similarities) < num_recommendations:
        num_recommendations = len(similarities)

    # 根据相似度对其他用户排序
    similarities.sort(key=lambda x: x[1], reverse=True)

    # 获取前num_recommendations个最相似用户的评分
    recommendations = []
    for i in range(num_recommendations):
        similar_user_index = similarities[i][0]
        similar_user_ratings = ratings[similar_user_index]
        for j in range(num_sections):
            # 过滤掉目标用户已经评价过的章节
            if target_user_ratings[j] == 0 and similar_user_ratings[j] != 0:
                recommendations.append((j, similar_user_ratings[j]))
        if len(recommendations) >= num_recommendations:
            break

    # 根据评分排序并返回推荐列表
    recommendations.sort(key=lambda x: x[1], reverse=True)
    return [section_index for section_index, _ in recommendations]


# 选择一个随机的用户来进行推荐
target_user_index = 0

# 获取推荐列表
recommended_sections = user_based_collaborative_filtering(target_user_index, ratings_matrix)

# 输出推荐列表
# 读取CSV文件
ratings = pd.read_csv('ratings.csv')

# 创建章节名称字典，将章节ID映射到章节名称
section_names = dict(zip(ratings['sectionId'], ratings['sectionname']))

# 在输出推荐列表时，使用章节名称代替索引
print("推荐给用户 {} 的章节：".format(target_user_index + 1))  # 用户ID从1开始，所以要加1
for i, section_index in enumerate(recommended_sections):
    section_name = section_names.get(section_index + 1, "未知章节")  # 获取电影名称，如果找不到则使用"未知电影"
    print("{}. {} (索引{})".format(i + 1, section_name, section_index + 1))  # 打印电影名称而不是索引
