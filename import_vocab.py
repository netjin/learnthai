import csv
import sys
from app import create_app, db
from app.models import Vocabulary

def import_from_csv(csv_file_path):
    """从 CSV 文件导入词汇"""
    app = create_app()
    with app.app_context():
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                skipped = 0

                for row in reader:
                    # 检查是否已存在
                    existing = Vocabulary.query.filter_by(
                        thai_word=row['thai_word']
                    ).first()

                    if existing:
                        print(f"⊘ 跳过重复词汇: {row['thai_word']}")
                        skipped += 1
                        continue

                    difficulty = row.get('difficulty_level', '1')
                    vocab = Vocabulary(
                        thai_word=row['thai_word'],
                        chinese_meaning=row['chinese_meaning'],
                        pronunciation=row.get('pronunciation', ''),
                        category=row.get('category', ''),
                        difficulty_level=int(difficulty) if difficulty else 1,
                        audio_file=row.get('audio_file', ''),
                        example_sentence_thai=row.get('example_thai', ''),
                        example_sentence_chinese=row.get('example_chinese', '')
                    )
                    db.session.add(vocab)
                    count += 1

                db.session.commit()
                print(f"\n✓ 成功导入 {count} 个词汇")
                if skipped:
                    print(f"⊘ 跳过 {skipped} 个重复词汇")

        except FileNotFoundError:
            print(f"✗ 错误：文件 '{csv_file_path}' 未找到")
            sys.exit(1)
        except Exception as e:
            print(f"✗ 导入失败: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python import_vocab.py <csv文件路径>")
        sys.exit(1)

    import_from_csv(sys.argv[1])
