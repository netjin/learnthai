"""导入泰语字母数据（44辅音 + 32元音）"""
from app import create_app, db
from app.models import ThaiAlphabet

# 44个泰语辅音
# (字符, 泰语名称, 中文名称, 罗马音, 音值, 辅音类别, 示例词, 示例中文)
CONSONANTS = [
    # 中辅音 (9个)
    ("ก", "ก ไก่", "鸡", "ko kai", "k", "mid", "ไก่", "鸡"),
    ("จ", "จ จาน", "盘子", "jo jan", "j", "mid", "จาน", "盘子"),
    ("ฎ", "ฎ ชฎา", "头冠", "do cha-da", "d", "mid", "ชฎา", "头冠"),
    ("ฏ", "ฏ ปฏัก", "枪", "to pa-tak", "t", "mid", "ปฏัก", "枪"),
    ("ด", "ด เด็ก", "孩子", "do dek", "d", "mid", "เด็ก", "孩子"),
    ("ต", "ต เต่า", "乌龟", "to tao", "t", "mid", "เต่า", "乌龟"),
    ("บ", "บ ใบไม้", "树叶", "bo bai-mai", "b", "mid", "ใบไม้", "树叶"),
    ("ป", "ป ปลา", "鱼", "po pla", "p", "mid", "ปลา", "鱼"),
    ("อ", "อ อ่าง", "盆", "o ang", "ʔ", "mid", "อ่าง", "盆"),

    # 高辅音 (11个)
    ("ข", "ข ไข่", "蛋", "kho khai", "kh", "high", "ไข่", "蛋"),
    ("ฃ", "ฃ ขวด", "瓶子", "kho khuat", "kh", "high", "ขวด", "瓶子"),
    ("ฉ", "ฉ ฉิ่ง", "钹", "cho ching", "ch", "high", "ฉิ่ง", "钹"),
    ("ฐ", "ฐ ฐาน", "底座", "tho than", "th", "high", "ฐาน", "底座"),
    ("ถ", "ถ ถุง", "袋子", "tho thung", "th", "high", "ถุง", "袋子"),
    ("ผ", "ผ ผึ้ง", "蜜蜂", "pho phueng", "ph", "high", "ผึ้ง", "蜜蜂"),
    ("ฝ", "ฝ ฝา", "盖子", "fo fa", "f", "high", "ฝา", "盖子"),
    ("ศ", "ศ ศาลา", "亭子", "so sala", "s", "high", "ศาลา", "亭子"),
    ("ษ", "ษ ฤๅษี", "隐士", "so rue-si", "s", "high", "ฤๅษี", "隐士"),
    ("ส", "ส เสือ", "老虎", "so suea", "s", "high", "เสือ", "老虎"),
    ("ห", "ห หีบ", "箱子", "ho hip", "h", "high", "หีบ", "箱子"),

    # 低辅音 (24个)
    ("ค", "ค ควาย", "水牛", "kho khwai", "kh", "low", "ควาย", "水牛"),
    ("ฅ", "ฅ คน", "人", "kho khon", "kh", "low", "คน", "人"),
    ("ฆ", "ฆ ระฆัง", "钟", "kho ra-khang", "kh", "low", "ระฆัง", "钟"),
    ("ง", "ง งู", "蛇", "ngo ngu", "ng", "low", "งู", "蛇"),
    ("ช", "ช ช้าง", "大象", "cho chang", "ch", "low", "ช้าง", "大象"),
    ("ซ", "ซ โซ่", "链条", "so so", "s", "low", "โซ่", "链条"),
    ("ฌ", "ฌ เฌอ", "树", "cho choe", "ch", "low", "เฌอ", "树"),
    ("ญ", "ญ หญิง", "女人", "yo ying", "y", "low", "หญิง", "女人"),
    ("ฑ", "ฑ มณโฑ", "皇后", "tho mon-tho", "th", "low", "มณโฑ", "皇后"),
    ("ฒ", "ฒ ผู้เฒ่า", "老人", "tho phu-thao", "th", "low", "ผู้เฒ่า", "老人"),
    ("ณ", "ณ เณร", "沙弥", "no nen", "n", "low", "เณร", "沙弥"),
    ("ท", "ท ทหาร", "士兵", "tho tha-han", "th", "low", "ทหาร", "士兵"),
    ("ธ", "ธ ธง", "旗帜", "tho thong", "th", "low", "ธง", "旗帜"),
    ("น", "น หนู", "老鼠", "no nu", "n", "low", "หนู", "老鼠"),
    ("พ", "พ พาน", "托盘", "pho phan", "ph", "low", "พาน", "托盘"),
    ("ฟ", "ฟ ฟัน", "牙齿", "fo fan", "f", "low", "ฟัน", "牙齿"),
    ("ภ", "ภ สำเภา", "帆船", "pho sam-phao", "ph", "low", "สำเภา", "帆船"),
    ("ม", "ม ม้า", "马", "mo ma", "m", "low", "ม้า", "马"),
    ("ย", "ย ยักษ์", "夜叉", "yo yak", "y", "low", "ยักษ์", "夜叉"),
    ("ร", "ร เรือ", "船", "ro ruea", "r", "low", "เรือ", "船"),
    ("ล", "ล ลิง", "猴子", "lo ling", "l", "low", "ลิง", "猴子"),
    ("ว", "ว แหวน", "戒指", "wo waen", "w", "low", "แหวน", "戒指"),
    ("ฬ", "ฬ จุฬา", "风筝", "lo chu-la", "l", "low", "จุฬา", "风筝"),
    ("ฮ", "ฮ นกฮูก", "猫头鹰", "ho nok-huk", "h", "low", "นกฮูก", "猫头鹰"),
]

# 32个泰语元音
# (字符, 泰语名称, 中文描述, 罗马音, 音值, 元音类型)
VOWELS = [
    # 短元音
    ("ะ", "สระ อะ", "短元音 a", "a", "a", "short"),
    ("ิ", "สระ อิ", "短元音 i", "i", "i", "short"),
    ("ึ", "สระ อึ", "短元音 ue", "ue", "ɯ", "short"),
    ("ุ", "สระ อุ", "短元音 u", "u", "u", "short"),
    ("เ-ะ", "สระ เอะ", "短元音 e", "e", "e", "short"),
    ("แ-ะ", "สระ แอะ", "短元音 ae", "ae", "ɛ", "short"),
    ("โ-ะ", "สระ โอะ", "短元音 o", "o", "o", "short"),
    ("เ-าะ", "สระ เอาะ", "短元音 o", "o", "ɔ", "short"),
    ("เ-อะ", "สระ เออะ", "短元音 oe", "oe", "ɤ", "short"),

    # 长元音
    ("า", "สระ อา", "长元音 aa", "aa", "aː", "long"),
    ("ี", "สระ อี", "长元音 ii", "ii", "iː", "long"),
    ("ื", "สระ อือ", "长元音 uue", "uue", "ɯː", "long"),
    ("ู", "สระ อู", "长元音 uu", "uu", "uː", "long"),
    ("เ-", "สระ เอ", "长元音 ee", "ee", "eː", "long"),
    ("แ-", "สระ แอ", "长元音 aae", "aae", "ɛː", "long"),
    ("โ-", "สระ โอ", "长元音 oo", "oo", "oː", "long"),
    ("-อ", "สระ ออ", "长元音 oo", "oo", "ɔː", "long"),
    ("เ-อ", "สระ เออ", "长元音 ooe", "ooe", "ɤː", "long"),

    # 复合元音
    ("เ-ีย", "สระ เอีย", "复合元音 ia", "ia", "ia", "compound"),
    ("เ-ือ", "สระ เอือ", "复合元音 uea", "uea", "ɯa", "compound"),
    ("-ัว", "สระ อัว", "复合元音 ua", "ua", "ua", "compound"),
    ("ใ-", "สระ ใอ", "复合元音 ai", "ai", "ai", "compound"),
    ("ไ-", "สระ ไอ", "复合元音 ai", "ai", "ai", "compound"),
    ("เ-า", "สระ เอา", "复合元音 ao", "ao", "ao", "compound"),
    ("-ำ", "สระ อำ", "复合元音 am", "am", "am", "compound"),

    # 特殊元音
    ("ฤ", "สระ ฤ", "特殊元音 rue", "rue", "rɯ", "special"),
    ("ฤๅ", "สระ ฤๅ", "特殊元音 ruue", "ruue", "rɯː", "special"),
    ("ฦ", "สระ ฦ", "特殊元音 lue", "lue", "lɯ", "special"),
    ("ฦๅ", "สระ ฦๅ", "特殊元音 luue", "luue", "lɯː", "special"),

    # 短复合元音
    ("เ-ียะ", "สระ เอียะ", "短复合元音 ia", "ia", "ia", "short_compound"),
    ("เ-ือะ", "สระ เอือะ", "短复合元音 uea", "uea", "ɯa", "short_compound"),
    ("-ัวะ", "สระ อัวะ", "短复合元音 ua", "ua", "ua", "short_compound"),
]


def import_alphabets():
    app = create_app()
    with app.app_context():
        added = 0
        skipped = 0

        # 导入辅音
        for i, (char, name_th, name_cn, pron, sound, con_class, ex_word, ex_mean) in enumerate(CONSONANTS):
            exists = ThaiAlphabet.query.filter_by(character=char, alphabet_type='consonant').first()
            if exists:
                skipped += 1
                continue

            alphabet = ThaiAlphabet(
                character=char,
                name_thai=name_th,
                name_chinese=name_cn,
                pronunciation=pron,
                sound=sound,
                alphabet_type='consonant',
                consonant_class=con_class,
                example_word=ex_word,
                example_meaning=ex_mean,
                sort_order=i + 1,
                is_active=True
            )
            db.session.add(alphabet)
            added += 1

        # 导入元音
        for i, (char, name_th, name_cn, pron, sound, v_type) in enumerate(VOWELS):
            exists = ThaiAlphabet.query.filter_by(character=char, alphabet_type='vowel').first()
            if exists:
                skipped += 1
                continue

            alphabet = ThaiAlphabet(
                character=char,
                name_thai=name_th,
                name_chinese=name_cn,
                pronunciation=pron,
                sound=sound,
                alphabet_type='vowel',
                vowel_type=v_type,
                sort_order=i + 1,
                is_active=True
            )
            db.session.add(alphabet)
            added += 1

        db.session.commit()

        # 统计
        consonant_count = ThaiAlphabet.query.filter_by(alphabet_type='consonant').count()
        vowel_count = ThaiAlphabet.query.filter_by(alphabet_type='vowel').count()

        print(f"新增: {added} 个字母")
        print(f"跳过: {skipped} 个重复")
        print(f"辅音总数: {consonant_count}")
        print(f"元音总数: {vowel_count}")


if __name__ == '__main__':
    import_alphabets()
