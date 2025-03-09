from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Пример текстов
text1 = "Первый текст для анализа"
text2 = "Второй текст для анализа"

# Токенизация текстов
tokenized_text1 = text1.lower().split()
tokenized_text2 = text2.lower().split()

# Создание корпуса текстов
corpus = [tokenized_text1, tokenized_text2]

# Обучение модели Word2Vec
model = Word2Vec(sentences=corpus, vector_size=100, window=5, min_count=1, workers=4)

# Получение векторных представлений текстов
def get_vector(text, model):
    # Усреднение векторов слов в тексте
    vectors = [model.wv[word] for word in text if word in model.wv]
    if not vectors:
        return np.zeros(model.vector_size)
    return np.mean(vectors, axis=0)

vector1 = get_vector(tokenized_text1, model)
vector2 = get_vector(tokenized_text2, model)

# Вычисление косинусного сходства
similarity = cosine_similarity([vector1], [vector2])[0][0]

print(f"Косинусное сходство: {similarity}")