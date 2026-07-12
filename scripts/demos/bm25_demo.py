import math
from collections import Counter
import re

# Một ví dụ đơn giản (Simple implementation) của thuật toán BM25 
# để giải thích cách tính điểm (Giúp báo cáo và người đọc dễ hiểu bản chất)

class BM25Demo:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.doc_len = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_len) / len(corpus)
        self.doc_freqs = []
        self.idf = {}
        self.doc_num = len(corpus)
        self._initialize()

    def _initialize(self):
        # Đếm tần suất từ (Term Frequency) trong mỗi tài liệu
        df = {}
        for document in self.corpus:
            frequencies = Counter(document)
            self.doc_freqs.append(frequencies)
            for word in frequencies:
                df[word] = df.get(word, 0) + 1

        # Tính toán IDF (Inverse Document Frequency)
        for word, freq in df.items():
            self.idf[word] = math.log(1 + (self.doc_num - freq + 0.5) / (freq + 0.5))

    def get_score(self, query, index):
        score = 0
        doc_freq = self.doc_freqs[index]
        for word in query:
            if word not in doc_freq:
                continue
            # TF của từ trong tài liệu index
            f = doc_freq[word]
            # Tính IDF
            idf = self.idf[word]
            # Công thức BM25
            numerator = f * (self.k1 + 1)
            denominator = f + self.k1 * (1 - self.b + self.b * self.doc_len[index] / self.avgdl)
            score += idf * (numerator / denominator)
        return score

    def get_scores(self, query):
        return [self.get_score(query, index) for index in range(self.doc_num)]

def tokenize(text):
    """ Hàm tách từ cơ bản bằng tiếng Việt (chữ thường, bỏ dấu câu đơn giản) """
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.split()

if __name__ == "__main__":
    print("="*60)
    print("DEMO THUẬT TOÁN BM25 (KEYWORD SEARCH - TUẦN 6)")
    print("="*60)
    
    # 1. Tập tài liệu mẫu (Corpus)
    documents = [
        "Công ty Cổ phần VNG công bố báo cáo tài chính quý 1 năm 2024",
        "Báo cáo tình hình kinh doanh của Vinamilk trong năm 2023 rất khả quan",
        "AI Agent và LLM là xu hướng công nghệ nổi bật của năm nay",
        "Hướng dẫn thiết lập hệ thống RAG và Vector Database cho ứng dụng AI",
        "Doanh thu báo cáo tài chính của tập đoàn FPT tăng trưởng mạnh"
    ]
    
    print("\n[TẬP TÀI LIỆU (CORPUS)]")
    for i, doc in enumerate(documents):
        print(f"Doc {i}: {doc}")
        
    # 2. Tokenize dữ liệu
    tokenized_corpus = [tokenize(doc) for doc in documents]
    
    # 3. Khởi tạo thuật toán BM25
    bm25 = BM25Demo(tokenized_corpus)
    
    # 4. Truy vấn thử nghiệm
    query_text = "báo cáo tài chính"
    print(f"\n[TRUY VẤN (QUERY)]: '{query_text}'")
    
    tokenized_query = tokenize(query_text)
    print(f"-> Tokens: {tokenized_query}")
    
    # 5. Tính điểm BM25 cho tất cả các tài liệu
    scores = bm25.get_scores(tokenized_query)
    
    print("\n[KẾT QUẢ ĐIỂM SỐ BM25]")
    for i, score in enumerate(scores):
        print(f"Doc {i} - Score: {score:.4f} => {documents[i]}")
        
    # 6. Sắp xếp kết quả
    print("\n[TÌM KIẾM THEO ĐỘ PHÙ HỢP (TOP 3)]")
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    for rank, idx in enumerate(ranked_indices[:3]):
        print(f"Top {rank+1}: Doc {idx} (Score: {scores[idx]:.4f}) - {documents[idx]}")
