import csv
import random

# 读取电影名称文件
movie_names = {}
with open('out_genre_section.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        movie_names[row[1]] = row[0]

# 生成评分数据并写入CSV文件
num_users = 200
num_movies_per_user = 50

with open('ratings.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['userId', 'movieId', 'rating', 'moviename']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for user_id in range(1, num_users + 1):
        # 为每个用户生成评分
        for _ in range(num_movies_per_user):
            movie_id = random.choice(list(movie_names.keys()))
            rating = round(random.uniform(0, 5), 2)
            moviename = movie_names[movie_id]
            writer.writerow({'userId': user_id, 'movieId': movie_id, 'rating': rating, 'moviename': moviename})

print("CSV文件已生成！")