#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入扩展的生活场景对话数据 - 每个场景10个对话
"""
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import ConversationScene, Conversation, ConversationLine

def clear_existing_data():
    """清除现有对话数据"""
    print("清除现有对话数据...")
    ConversationLine.query.delete()
    Conversation.query.delete()
    ConversationScene.query.delete()
    db.session.commit()
    print("✓ 清除完成")

def import_extended_conversations():
    """导入扩展的对话数据"""
    app = create_app()
    
    with app.app_context():
        print("\n开始导入扩展的生活场景对话数据...")
        
        # 清除现有数据
        clear_existing_data()
        
        # ==================== 场景1: 餐厅点餐 ====================
        scene1 = ConversationScene(
            name_chinese="餐厅点餐",
            name_thai="สั่งอาหารที่ร้านอาหาร",
            icon="🍽️",
            description="学习在泰国餐厅点餐的常用对话",
            difficulty_level=1,
            sort_order=1
        )
        db.session.add(scene1)
        db.session.flush()
        
        # 对话1: 预订餐位
        conv1_1 = Conversation(
            scene_id=scene1.id,
            title_chinese="预订餐位",
            title_thai="จองโต๊ะอาหาร",
            situation="顾客打电话预订晚餐餐位",
            difficulty_level=1,
            sort_order=1
        )
        db.session.add(conv1_1)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv1_1.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="สวัสดีครับ ผมอยากจองโต๊ะสำหรับคืนนี้ครับ", text_chinese="您好，我想预订今晚的餐位",
                pronunciation="sa-wat-dee krap, pom yaak jong toh sam-rap keun nee krap",
                key_words=json.dumps(["จอง", "โต๊ะ"])),
            ConversationLine(conversation_id=conv1_1.id, line_order=2, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="ได้ครับ กี่ท่านครับ", text_chinese="好的，请问几位？",
                pronunciation="dai krap, gee tan krap", key_words=json.dumps(["กี่ท่าน"])),
            ConversationLine(conversation_id=conv1_1.id, line_order=3, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="สี่ท่านครับ เวลาสามทุ่มครับ", text_chinese="四位，晚上9点",
                pronunciation="see tan krap, we-la sam toom krap", key_words=json.dumps(["สี่ท่าน", "สามทุ่ม"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话2: 点菜
        conv1_2 = Conversation(scene_id=scene1.id, title_chinese="点菜", title_thai="สั่งอาหาร",
            situation="在餐厅点菜", difficulty_level=1, sort_order=2)
        db.session.add(conv1_2)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv1_2.id, line_order=1, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="สั่งอะไรดีครับ", text_chinese="请问要点什么？",
                pronunciation="sang a-rai dee krap", key_words=json.dumps(["สั่ง", "อะไร"])),
            ConversationLine(conversation_id=conv1_2.id, line_order=2, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="ขอผัดไทยหนึ่งจานครับ", text_chinese="我要一份泰式炒河粉",
                pronunciation="kor pad thai neung jan krap", key_words=json.dumps(["ผัดไทย", "หนึ่งจาน"])),
            ConversationLine(conversation_id=conv1_2.id, line_order=3, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="เอาเผ็ดไหมครับ", text_chinese="要辣的吗？",
                pronunciation="ao pet mai krap", key_words=json.dumps(["เผ็ด"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话3: 询问菜品
        conv1_3 = Conversation(scene_id=scene1.id, title_chinese="询问菜品", title_thai="ถามเมนู",
            situation="询问服务员推荐菜品", difficulty_level=1, sort_order=3)
        db.session.add(conv1_3)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv1_3.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="มีอะไรแนะนำบ้างครับ", text_chinese="有什么推荐的吗？",
                pronunciation="mee a-rai nae-nam bang krap", key_words=json.dumps(["แนะนำ"])),
            ConversationLine(conversation_id=conv1_3.id, line_order=2, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="ต้มยำกุ้งของเราอร่อยมากค่ะ", text_chinese="我们的冬阴功汤很好吃",
                pronunciation="tom yam goong kong rao a-roi mak ka", key_words=json.dumps(["ต้มยำกุ้ง", "อร่อย"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话4: 要求结账
        conv1_4 = Conversation(scene_id=scene1.id, title_chinese="结账", title_thai="เช็คบิล",
            situation="用餐后要求结账", difficulty_level=1, sort_order=4)
        db.session.add(conv1_4)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv1_4.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="ขอเช็คบิลด้วยครับ", text_chinese="请结账",
                pronunciation="kor check bin duay krap", key_words=json.dumps(["เช็คบิล"])),
            ConversationLine(conversation_id=conv1_4.id, line_order=2, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="รวมทั้งหมดห้าร้อยบาทค่ะ", text_chinese="一共500泰铢",
                pronunciation="ruam tang mot ha roi baht ka", key_words=json.dumps(["รวม", "ห้าร้อยบาท"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话5: 询问营业时间
        conv1_5 = Conversation(scene_id=scene1.id, title_chinese="询问营业时间", title_thai="ถามเวลาทำการ",
            situation="询问餐厅营业时间", difficulty_level=1, sort_order=5)
        db.session.add(conv1_5)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv1_5.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="ร้านเปิดกี่โมงครับ", text_chinese="餐厅几点开门？",
                pronunciation="ran poet gee mong krap", key_words=json.dumps(["เปิด", "กี่โมง"])),
            ConversationLine(conversation_id=conv1_5.id, line_order=2, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="เปิดตั้งแต่สิบโมงเช้าถึงสี่ทุ่มค่ะ", text_chinese="从早上10点到晚上10点",
                pronunciation="poet tang tae sip mong chao teung see toom ka",
                key_words=json.dumps(["สิบโมงเช้า", "สี่ทุ่ม"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话6: 点饮料
        conv1_6 = Conversation(scene_id=scene1.id, title_chinese="点饮料", title_thai="สั่งเครื่องดื่ม",
            situation="点饮料", difficulty_level=1, sort_order=6)
        db.session.add(conv1_6)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv1_6.id, line_order=1, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="ดื่มอะไรดีคะ", text_chinese="要喝什么？",
                pronunciation="deum a-rai dee ka", key_words=json.dumps(["ดื่ม"])),
            ConversationLine(conversation_id=conv1_6.id, line_order=2, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="ขอน้ำส้มสองแก้วครับ", text_chinese="要两杯橙汁",
                pronunciation="kor nam som song gaew krap", key_words=json.dumps(["น้ำส้ม", "สองแก้ว"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话7: 要求打包
        conv1_7 = Conversation(scene_id=scene1.id, title_chinese="打包", title_thai="ห่อกลับบ้าน",
            situation="要求将剩菜打包", difficulty_level=1, sort_order=7)
        db.session.add(conv1_7)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv1_7.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="ขอห่อกลับบ้านได้ไหมครับ", text_chinese="可以打包吗？",
                pronunciation="kor hor glap ban dai mai krap", key_words=json.dumps(["ห่อกลับบ้าน"])),
            ConversationLine(conversation_id=conv1_7.id, line_order=2, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="ได้ค่ะ รอสักครู่นะคะ", text_chinese="可以，请稍等",
                pronunciation="dai ka, ror sak kru na ka", key_words=json.dumps(["รอสักครู่"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话8: 询问WiFi密码
        conv1_8 = Conversation(scene_id=scene1.id, title_chinese="询问WiFi", title_thai="ถามรหัส WiFi",
            situation="询问餐厅WiFi密码", difficulty_level=1, sort_order=8)
        db.session.add(conv1_8)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv1_8.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="มี WiFi ไหมครับ", text_chinese="有WiFi吗？",
                pronunciation="mee WiFi mai krap", key_words=json.dumps(["WiFi"])),
            ConversationLine(conversation_id=conv1_8.id, line_order=2, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="มีค่ะ รหัสคือ 12345678 ค่ะ", text_chinese="有的，密码是12345678",
                pronunciation="mee ka, ra-hat keu 12345678 ka", key_words=json.dumps(["รหัส"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话9: 投诉菜品
        conv1_9 = Conversation(scene_id=scene1.id, title_chinese="反馈问题", title_thai="แจ้งปัญหา",
            situation="菜品有问题需要反馈", difficulty_level=2, sort_order=9)
        db.session.add(conv1_9)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv1_9.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="ขอโทษครับ อาหารเย็นไปหน่อยครับ", text_chinese="不好意思，菜有点凉了",
                pronunciation="kor toht krap, a-han yen pai noi krap",
                key_words=json.dumps(["อาหาร", "เย็น"])),
            ConversationLine(conversation_id=conv1_9.id, line_order=2, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="ขอโทษค่ะ ดิฉันจะเอาไปอุ่นใหม่ให้นะคะ", text_chinese="对不起，我帮您重新加热",
                pronunciation="kor toht ka, di-chan ja ao pai un mai hai na ka",
                key_words=json.dumps(["อุ่นใหม่"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话10: 称赞菜品
        conv1_10 = Conversation(scene_id=scene1.id, title_chinese="称赞菜品", title_thai="ชมอาหาร",
            situation="对美味的菜品表示称赞", difficulty_level=1, sort_order=10)
        db.session.add(conv1_10)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv1_10.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="อาหารอร่อยมากครับ", text_chinese="菜很好吃",
                pronunciation="a-han a-roi mak krap", key_words=json.dumps(["อาหาร", "อร่อยมาก"])),
            ConversationLine(conversation_id=conv1_10.id, line_order=2, speaker_role="服务员", speaker_role_thai="พนักงาน",
                text_thai="ขอบคุณมากค่ะ ยินดีต้อนรับค่ะ", text_chinese="非常感谢，欢迎光临",
                pronunciation="kop kun mak ka, yin dee ton rap ka",
                key_words=json.dumps(["ขอบคุณ", "ยินดีต้อนรับ"])),
        ]
        for line in lines:
            db.session.add(line)
        
        print(f"✓ 场景1【餐厅点餐】: 10个对话")
        
        # ==================== 场景2: 购物 ====================
        scene2 = ConversationScene(
            name_chinese="购物",
            name_thai="ซื้อของ",
            icon="🛍️",
            description="学习在商店购物的常用对话",
            difficulty_level=1,
            sort_order=2
        )
        db.session.add(scene2)
        db.session.flush()
        
        # 对话1: 询问价格
        conv2_1 = Conversation(scene_id=scene2.id, title_chinese="询问价格", title_thai="ถามราคา",
            situation="在市场询问商品价格", difficulty_level=1, sort_order=1)
        db.session.add(conv2_1)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv2_1.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="อันนี้ราคาเท่าไหร่ครับ", text_chinese="这个多少钱？",
                pronunciation="an nee ra-ka tao-rai krap", key_words=json.dumps(["ราคา", "เท่าไหร่"])),
            ConversationLine(conversation_id=conv2_1.id, line_order=2, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="สองร้อยบาทค่ะ", text_chinese="200泰铢",
                pronunciation="song roi baht ka", key_words=json.dumps(["สองร้อยบาท"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话2: 讨价还价
        conv2_2 = Conversation(scene_id=scene2.id, title_chinese="讨价还价", title_thai="ต่อราคา",
            situation="在市场讨价还价", difficulty_level=1, sort_order=2)
        db.session.add(conv2_2)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv2_2.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="แพงไปหน่อยนะครับ ลดได้ไหมครับ", text_chinese="有点贵，能便宜点吗？",
                pronunciation="paeng pai noi na krap, lot dai mai krap",
                key_words=json.dumps(["แพง", "ลด"])),
            ConversationLine(conversation_id=conv2_2.id, line_order=2, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="ลดให้หนึ่งร้อยแปดสิบบาทค่ะ", text_chinese="给你便宜到180泰铢",
                pronunciation="lot hai neung roi paet sip baht ka",
                key_words=json.dumps(["ลด", "หนึ่งร้อยแปดสิบ"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话3: 试穿衣服
        conv2_3 = Conversation(scene_id=scene2.id, title_chinese="试穿衣服", title_thai="ลองเสื้อผ้า",
            situation="在服装店试穿衣服", difficulty_level=1, sort_order=3)
        db.session.add(conv2_3)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv2_3.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="ขอลองได้ไหมครับ", text_chinese="可以试穿吗？",
                pronunciation="kor long dai mai krap", key_words=json.dumps(["ลอง"])),
            ConversationLine(conversation_id=conv2_3.id, line_order=2, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="ได้ค่ะ ห้องลองอยู่ตรงนั้นค่ะ", text_chinese="可以，试衣间在那边",
                pronunciation="dai ka, hong long yu trong nan ka",
                key_words=json.dumps(["ห้องลอง"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话4: 询问尺码
        conv2_4 = Conversation(scene_id=scene2.id, title_chinese="询问尺码", title_thai="ถามไซส์",
            situation="询问衣服尺码", difficulty_level=1, sort_order=4)
        db.session.add(conv2_4)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv2_4.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="มีไซส์ M ไหมครับ", text_chinese="有M码吗？",
                pronunciation="mee size M mai krap", key_words=json.dumps(["ไซส์"])),
            ConversationLine(conversation_id=conv2_4.id, line_order=2, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="มีค่ะ รอสักครู่นะคะ", text_chinese="有的，请稍等",
                pronunciation="mee ka, ror sak kru na ka", key_words=json.dumps(["รอสักครู่"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话5: 询问颜色
        conv2_5 = Conversation(scene_id=scene2.id, title_chinese="询问颜色", title_thai="ถามสี",
            situation="询问商品其他颜色", difficulty_level=1, sort_order=5)
        db.session.add(conv2_5)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv2_5.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="มีสีอื่นไหมครับ", text_chinese="有其他颜色吗？",
                pronunciation="mee see eun mai krap", key_words=json.dumps(["สี", "อื่น"])),
            ConversationLine(conversation_id=conv2_5.id, line_order=2, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="มีสีดำและสีขาวค่ะ", text_chinese="有黑色和白色",
                pronunciation="mee see dam lae see kao ka",
                key_words=json.dumps(["สีดำ", "สีขาว"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话6: 付款
        conv2_6 = Conversation(scene_id=scene2.id, title_chinese="付款", title_thai="จ่ายเงิน",
            situation="在收银台付款", difficulty_level=1, sort_order=6)
        db.session.add(conv2_6)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv2_6.id, line_order=1, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="รวมสามร้อยบาทค่ะ", text_chinese="一共300泰铢",
                pronunciation="ruam sam roi baht ka", key_words=json.dumps(["รวม", "สามร้อยบาท"])),
            ConversationLine(conversation_id=conv2_6.id, line_order=2, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="รับบัตรเครดิตไหมครับ", text_chinese="收信用卡吗？",
                pronunciation="rap bat credit mai krap", key_words=json.dumps(["บัตรเครดิต"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话7: 要求退换货
        conv2_7 = Conversation(scene_id=scene2.id, title_chinese="退换货", title_thai="เปลี่ยนสินค้า",
            situation="商品有问题要求退换", difficulty_level=2, sort_order=7)
        db.session.add(conv2_7)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv2_7.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="ขอเปลี่ยนได้ไหมครับ ไซส์ไม่พอดีครับ", text_chinese="可以换吗？尺码不合适",
                pronunciation="kor plian dai mai krap, size mai por dee krap",
                key_words=json.dumps(["เปลี่ยน", "ไซส์ไม่พอดี"])),
            ConversationLine(conversation_id=conv2_7.id, line_order=2, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="ได้ค่ะ มีใบเสร็จไหมคะ", text_chinese="可以，有收据吗？",
                pronunciation="dai ka, mee bai set mai ka", key_words=json.dumps(["ใบเสร็จ"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话8: 询问促销
        conv2_8 = Conversation(scene_id=scene2.id, title_chinese="询问促销", title_thai="ถามโปรโมชั่น",
            situation="询问是否有促销活动", difficulty_level=1, sort_order=8)
        db.session.add(conv2_8)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv2_8.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="วันนี้มีโปรโมชั่นไหมครับ", text_chinese="今天有促销吗？",
                pronunciation="wan nee mee promotion mai krap", key_words=json.dumps(["โปรโมชั่น"])),
            ConversationLine(conversation_id=conv2_8.id, line_order=2, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="มีค่ะ ซื้อสองชิ้นลดสิบเปอร์เซ็นต์ค่ะ", text_chinese="有的，买两件打九折",
                pronunciation="mee ka, seu song chin lot sip percent ka",
                key_words=json.dumps(["ซื้อสองชิ้น", "ลดสิบเปอร์เซ็นต์"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话9: 询问营业时间
        conv2_9 = Conversation(scene_id=scene2.id, title_chinese="询问营业时间", title_thai="ถามเวลาเปิด-ปิด",
            situation="询问商店营业时间", difficulty_level=1, sort_order=9)
        db.session.add(conv2_9)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv2_9.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="ร้านปิดกี่โมงครับ", text_chinese="商店几点关门？",
                pronunciation="ran pit gee mong krap", key_words=json.dumps(["ปิด", "กี่โมง"])),
            ConversationLine(conversation_id=conv2_9.id, line_order=2, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="ปิดห้าทุ่มค่ะ", text_chinese="晚上11点关门",
                pronunciation="pit ha toom ka", key_words=json.dumps(["ห้าทุ่ม"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话10: 询问推荐
        conv2_10 = Conversation(scene_id=scene2.id, title_chinese="询问推荐", title_thai="ขอคำแนะนำ",
            situation="询问店员推荐商品", difficulty_level=1, sort_order=10)
        db.session.add(conv2_10)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv2_10.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="แนะนำอะไรดีครับ", text_chinese="推荐什么好？",
                pronunciation="nae-nam a-rai dee krap", key_words=json.dumps(["แนะนำ"])),
            ConversationLine(conversation_id=conv2_10.id, line_order=2, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="ตัวนี้เป็นที่นิยมมากค่ะ", text_chinese="这款很受欢迎",
                pronunciation="tua nee pen tee ni-yom mak ka",
                key_words=json.dumps(["ที่นิยม"])),
        ]
        for line in lines:
            db.session.add(line)
        
        print(f"✓ 场景2【购物】: 10个对话")
        
        # ==================== 场景3: 交通出行 ====================
        scene3 = ConversationScene(
            name_chinese="交通出行",
            name_thai="การเดินทาง",
            icon="🚕",
            description="学习乘坐交通工具的常用对话",
            difficulty_level=2,
            sort_order=3
        )
        db.session.add(scene3)
        db.session.flush()
        
        # 对话1: 打车
        conv3_1 = Conversation(scene_id=scene3.id, title_chinese="打车", title_thai="เรียกแท็กซี่",
            situation="在路边打出租车", difficulty_level=2, sort_order=1)
        db.session.add(conv3_1)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv3_1.id, line_order=1, speaker_role="乘客", speaker_role_thai="ผู้โดยสาร",
                text_thai="ไปสยามพารากอนครับ", text_chinese="去暹罗百丽宫",
                pronunciation="pai siam paragon krap", key_words=json.dumps(["ไป", "สยามพารากอน"])),
            ConversationLine(conversation_id=conv3_1.id, line_order=2, speaker_role="司机", speaker_role_thai="คนขับ",
                text_thai="ได้ครับ ขึ้นมาเลยครับ", text_chinese="好的，请上车",
                pronunciation="dai krap, keun ma loey krap", key_words=json.dumps(["ขึ้นมา"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话2: 询问路线
        conv3_2 = Conversation(scene_id=scene3.id, title_chinese="询问路线", title_thai="ถามเส้นทาง",
            situation="询问司机走哪条路", difficulty_level=2, sort_order=2)
        db.session.add(conv3_2)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv3_2.id, line_order=1, speaker_role="乘客", speaker_role_thai="ผู้โดยสาร",
                text_thai="ไปทางไหนดีครับ", text_chinese="走哪条路好？",
                pronunciation="pai tang nai dee krap", key_words=json.dumps(["ทาง", "ไหน"])),
            ConversationLine(conversation_id=conv3_2.id, line_order=2, speaker_role="司机", speaker_role_thai="คนขับ",
                text_thai="ผมจะไปทางด่วนครับ เร็วกว่าครับ", text_chinese="我走高速，比较快",
                pronunciation="pom ja pai tang duan krap, reo gwa krap",
                key_words=json.dumps(["ทางด่วน", "เร็ว"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话3: 询问车费
        conv3_3 = Conversation(scene_id=scene3.id, title_chinese="询问车费", title_thai="ถามค่าโดยสาร",
            situation="询问出租车费用", difficulty_level=2, sort_order=3)
        db.session.add(conv3_3)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv3_3.id, line_order=1, speaker_role="乘客", speaker_role_thai="ผู้โดยสาร",
                text_thai="ไปที่นั่นเท่าไหร่ครับ", text_chinese="去那里多少钱？",
                pronunciation="pai tee nan tao-rai krap", key_words=json.dumps(["เท่าไหร่"])),
            ConversationLine(conversation_id=conv3_3.id, line_order=2, speaker_role="司机", speaker_role_thai="คนขับ",
                text_thai="ประมาณหนึ่งร้อยบาทครับ", text_chinese="大约100泰铢",
                pronunciation="pra-man neung roi baht krap",
                key_words=json.dumps(["ประมาณ", "หนึ่งร้อยบาท"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话4: 乘坐BTS
        conv3_4 = Conversation(scene_id=scene3.id, title_chinese="乘坐BTS", title_thai="นั่ง BTS",
            situation="在BTS站台买票", difficulty_level=2, sort_order=4)
        db.session.add(conv3_4)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv3_4.id, line_order=1, speaker_role="乘客", speaker_role_thai="ผู้โดยสาร",
                text_thai="ไปสยามกี่บาทครับ", text_chinese="去暹罗多少钱？",
                pronunciation="pai siam gee baht krap", key_words=json.dumps(["ไปสยาม", "กี่บาท"])),
            ConversationLine(conversation_id=conv3_4.id, line_order=2, speaker_role="工作人员", speaker_role_thai="เจ้าหน้าที่",
                text_thai="สามสิบบาทค่ะ", text_chinese="30泰铢",
                pronunciation="sam sip baht ka", key_words=json.dumps(["สามสิบบาท"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话5: 问路
        conv3_5 = Conversation(scene_id=scene3.id, title_chinese="问路", title_thai="ถามทาง",
            situation="在街上问路", difficulty_level=2, sort_order=5)
        db.session.add(conv3_5)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv3_5.id, line_order=1, speaker_role="游客", speaker_role_thai="นักท่องเที่ยว",
                text_thai="ขอโทษครับ ห้างสรรพสินค้าอยู่ทางไหนครับ", text_chinese="不好意思，商场在哪边？",
                pronunciation="kor toht krap, hang sap-pa-sin-ka yu tang nai krap",
                key_words=json.dumps(["ห้างสรรพสินค้า", "ทางไหน"])),
            ConversationLine(conversation_id=conv3_5.id, line_order=2, speaker_role="路人", speaker_role_thai="คนทั่วไป",
                text_thai="ตรงไปแล้วเลี้ยวซ้ายครับ", text_chinese="直走然后左转",
                pronunciation="trong pai laew liao sai krap",
                key_words=json.dumps(["ตรงไป", "เลี้ยวซ้าย"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话6: 租摩托车
        conv3_6 = Conversation(scene_id=scene3.id, title_chinese="租摩托车", title_thai="เช่ามอเตอร์ไซค์",
            situation="在租车店租摩托车", difficulty_level=2, sort_order=6)
        db.session.add(conv3_6)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv3_6.id, line_order=1, speaker_role="顾客", speaker_role_thai="ลูกค้า",
                text_thai="เช่ามอเตอร์ไซค์วันละเท่าไหร่ครับ", text_chinese="租摩托车一天多少钱？",
                pronunciation="chao motor-sai wan la tao-rai krap",
                key_words=json.dumps(["เช่า", "วันละเท่าไหร่"])),
            ConversationLine(conversation_id=conv3_6.id, line_order=2, speaker_role="店员", speaker_role_thai="พนักงาน",
                text_thai="สองร้อยบาทต่อวันครับ", text_chinese="一天200泰铢",
                pronunciation="song roi baht tor wan krap",
                key_words=json.dumps(["สองร้อยบาท", "ต่อวัน"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话7: 叫Grab
        conv3_7 = Conversation(scene_id=scene3.id, title_chinese="叫网约车", title_thai="เรียก Grab",
            situation="使用Grab叫车", difficulty_level=2, sort_order=7)
        db.session.add(conv3_7)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv3_7.id, line_order=1, speaker_role="司机", speaker_role_thai="คนขับ",
                text_thai="คุณคือคุณหวังใช่ไหมครับ", text_chinese="您是王先生吗？",
                pronunciation="kun keu kun wang chai mai krap",
                key_words=json.dumps(["คุณคือ", "ใช่ไหม"])),
            ConversationLine(conversation_id=conv3_7.id, line_order=2, speaker_role="乘客", speaker_role_thai="ผู้โดยสาร",
                text_thai="ใช่ครับ ไปสนามบินสุวรรณภูมิครับ", text_chinese="是的，去素万那普机场",
                pronunciation="chai krap, pai sa-nam-bin suvarnabhumi krap",
                key_words=json.dumps(["สนามบิน", "สุวรรณภูมิ"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话8: 询问到达时间
        conv3_8 = Conversation(scene_id=scene3.id, title_chinese="询问到达时间", title_thai="ถามเวลาถึง",
            situation="询问司机多久能到", difficulty_level=2, sort_order=8)
        db.session.add(conv3_8)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv3_8.id, line_order=1, speaker_role="乘客", speaker_role_thai="ผู้โดยสาร",
                text_thai="ไปถึงกี่โมงครับ", text_chinese="几点能到？",
                pronunciation="pai teung gee mong krap", key_words=json.dumps(["ถึง", "กี่โมง"])),
            ConversationLine(conversation_id=conv3_8.id, line_order=2, speaker_role="司机", speaker_role_thai="คนขับ",
                text_thai="ประมาณครึ่งชั่วโมงครับ", text_chinese="大约半小时",
                pronunciation="pra-man kreung chua-mong krap",
                key_words=json.dumps(["ประมาณ", "ครึ่งชั่วโมง"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话9: 要求停车
        conv3_9 = Conversation(scene_id=scene3.id, title_chinese="要求停车", title_thai="ขอจอดรถ",
            situation="要求司机在某处停车", difficulty_level=2, sort_order=9)
        db.session.add(conv3_9)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv3_9.id, line_order=1, speaker_role="乘客", speaker_role_thai="ผู้โดยสาร",
                text_thai="ขอจอดตรงนี้ได้ไหมครับ", text_chinese="可以在这里停吗？",
                pronunciation="kor jot trong nee dai mai krap",
                key_words=json.dumps(["จอด", "ตรงนี้"])),
            ConversationLine(conversation_id=conv3_9.id, line_order=2, speaker_role="司机", speaker_role_thai="คนขับ",
                text_thai="ได้ครับ", text_chinese="可以",
                pronunciation="dai krap", key_words=json.dumps(["ได้"])),
        ]
        for line in lines:
            db.session.add(line)
        
        # 对话10: 给小费
        conv3_10 = Conversation(scene_id=scene3.id, title_chinese="给小费", title_thai="ให้ทิป",
            situation="付车费并给小费", difficulty_level=2, sort_order=10)
        db.session.add(conv3_10)
        db.session.flush()
        
        lines = [
            ConversationLine(conversation_id=conv3_10.id, line_order=1, speaker_role="乘客", speaker_role_thai="ผู้โดยสาร",
                text_thai="เก็บเงินทอนไว้เลยครับ", text_chinese="零钱不用找了",
                pronunciation="gep ngoen ton wai loey krap",
                key_words=json.dumps(["เงินทอน", "ไว้เลย"])),
            ConversationLine(conversation_id=conv3_10.id, line_order=2, speaker_role="司机", speaker_role_thai="คนขับ",
                text_thai="ขอบคุณมากครับ", text_chinese="非常感谢",
                pronunciation="kop kun mak krap", key_words=json.dumps(["ขอบคุณมาก"])),
        ]
        for line in lines:
            db.session.add(line)
        
        print(f"✓ 场景3【交通出行】: 10个对话")
        
        # 提交所有数据
        db.session.commit()
        
        print("\n" + "="*50)
        print("数据导入完成！")
        print("="*50)
        
        # 显示统计
        scene_count = ConversationScene.query.count()
        conv_count = Conversation.query.count()
        line_count = ConversationLine.query.count()
        
        print(f"\n📊 当前数据库统计:")
        print(f"   场景数: {scene_count}")
        print(f"   对话数: {conv_count}")
        print(f"   对话句子数: {line_count}")
        print(f"\n✅ 每个场景都包含10个对话！")

if __name__ == '__main__':
    import_extended_conversations()
