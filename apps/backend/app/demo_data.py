from __future__ import annotations

from .database import compile_preset, db, now, parse_json, record_version, to_json, to_json_array
from .services.character_schema import apply_player_visibility, build_default_visibility, default_character_data, normalize_character_contract


PROJECT_ID = "proj_demo"


def md(*sections: str) -> str:
    return "\n\n".join(section.strip() for section in sections if section.strip())


def insert_once(table: str, row_id: str, sql: str, params: tuple):
    if not db.one(f"SELECT id FROM {table} WHERE id = ?", (row_id,)):
        db.exec(sql, params)


def ensure_demo_character_gender(char_id: str, expected_developer: dict):
    row = db.one("SELECT developer_data, player_data, field_visibility FROM characters WHERE id = ?", (char_id,))
    if not row:
        return
    expected_gender = expected_developer.get("basic", {}).get("gender", "")
    developer = parse_json(row.get("developer_data"), {})
    player = parse_json(row.get("player_data"), {})
    visibility = parse_json(row.get("field_visibility"), {})
    basic = developer.setdefault("basic", {})
    player_basic = player.setdefault("basic", {})
    basic_visibility = visibility.setdefault("basic", {})
    if basic.get("gender") == expected_gender and player_basic.get("gender") == expected_gender and isinstance(basic_visibility.get("gender"), dict):
        return
    basic["gender"] = expected_gender
    player_basic["gender"] = expected_gender
    basic_visibility.setdefault("gender", {"visible": True, "displayMode": "full", "customDisplay": ""})
    normalized = normalize_character_contract({"name": basic.get("name", ""), "developer_data": developer, "player_data": player, "field_visibility": visibility})
    db.exec(
        "UPDATE characters SET developer_data = ?, player_data = ?, field_visibility = ?, updated_at = ? WHERE id = ?",
        (to_json(normalized["developer_data"]), to_json(normalized["player_data"]), to_json(normalized["field_visibility"]), now(), char_id),
    )


def ensure_category(category_id: str, name: str, description: str, order: int):
    stamp = now()
    insert_once(
        "worldbook_categories",
        category_id,
        """INSERT INTO worldbook_categories
           (id, project_id, parent_id, name, description, template, custom_fields, sort_order, created_at, updated_at)
           VALUES (?, ?, NULL, ?, ?, ?, '[]', ?, ?, ?)""",
        (
            category_id,
            PROJECT_ID,
            name,
            description,
            to_json(
                {
                    "sections": [
                        {"id": "definition", "title": "定义", "required": True, "aiHint": "定义设定边界"},
                        {"id": "rules", "title": "规则", "required": True, "aiHint": "说明系统规则与限制"},
                        {"id": "conflict", "title": "冲突", "required": False, "aiHint": "指出可用于剧情的冲突"},
                        {"id": "hooks", "title": "钩子", "required": False, "aiHint": "给出可扩展素材"},
                    ]
                }
            ),
            order,
            stamp,
            stamp,
        ),
    )


WORLD_ENTRIES = [
    (
        "world_lingxu_continent",
        "cat_geography",
        "灵墟九洲",
        ["地理", "九洲", "主舞台"],
        md(
            "## 定义\n灵墟九洲是本修仙世界的主体大陆群，由中洲、玄洲、澜洲、炎洲、朔洲、青洲、幽洲、辰洲与荒洲构成。九洲不是单纯地理区划，而是九条古代地脉在大灾变后重新凝结出的灵气生态。每一洲都有不同的灵脉浓度、天象周期、宗门格局和凡俗王朝，修士跨洲远行往往需要飞舟、传送阵或元婴以上修为。",
            "## 规则\n中洲灵脉最稳，是正道联盟与大型商会核心；玄洲多剑修；澜洲盛产水行丹材；炎洲地火不息，炼器最盛；朔洲苦寒，体修与阵修常在此磨砺；青洲多药谷灵田；幽洲常年阴雾，是鬼修与禁术潜伏地；辰洲观星台林立；荒洲则是上古战场和妖族古脉交错之地。",
            "## 冲突\n每隔三十六年地脉潮汐会改变灵气走向，导致宗门争矿、王朝迁都、散修暴动。宗门大会表面是礼仪，暗地里是灵脉分配谈判，伴随刺杀、婚盟、禁器交易和秘境名额交换。",
            "## 钩子\n古籍称九洲只是封印阵的九枚阵眼。若第十洲显化，意味着被镇压的天外真灵将重新接近人间。",
        ),
        {"definition": "九条地脉凝结的修仙大陆群", "conflict": "地脉潮汐引发资源战争"},
    ),
    (
        "world_cultivation_levels",
        "cat_systems",
        "修行境界体系",
        ["体系", "修炼", "境界"],
        md(
            "## 定义\n九洲通行境界分为炼气、筑基、金丹、元婴、化神、洞虚、合道、渡劫、大乘。境界不是单纯力量等级，而是修士与天地灵机建立联系的方式逐层深化：炼气纳灵入体，筑基铸道台，金丹凝命核，元婴分化神魂，化神与法则初步共鸣，洞虚触及空间裂隙。",
            "## 规则\n突破需要灵气、心境、功法、因果同时满足。最关键的是道基质量，劣等筑基即使升入金丹，也会在元婴时遭遇神魂分裂；完美筑基者可在低境界越级斗法。强行突破会形成道伤，道伤只能通过秘境机缘、功德抵偿或重修功法解决。",
            "## 冲突\n宗门用境界分配资源，但真正决定未来的是隐藏的道基质量。主角可以在境界不高时被轻视，又凭特殊道基反转。反派可掠夺他人道基快速晋升，制造道德和生存冲突。",
            "## 钩子\n传说九大境界之上还有问天境，但所有触及问天境的修士都会在史书中被抹去姓名。",
        ),
        {"levels": ["炼气", "筑基", "金丹", "元婴", "化神", "洞虚", "合道", "渡劫", "大乘"]},
    ),
    (
        "world_sky_seal",
        "cat_systems",
        "天阙封印",
        ["上古", "封印", "主线"],
        md(
            "## 定义\n天阙封印是覆盖九洲天穹的上古大阵，凡人只看见星河，化神修士才能感到天幕深处的无形压力。它由九洲地脉、十二座观星台和三十六件镇界灵宝共同维系，用于阻隔天外真灵直接降临，同时限制人间修士飞升。",
            "## 规则\n封印吸收大乘修士突破时逸散的道韵，因此越强的修士越容易成为封印燃料。正道称其为飞升天劫，魔道认为这是上古宗门牺牲后人的骗局。每当地脉潮汐衰弱，天阙会出现裂隙，落下星砂、异火或带污染的梦境。",
            "## 冲突\n维护封印意味着牺牲顶尖修士自由，破坏封印则可能释放天外灾厄。主角真正要寻找的是第三条路：重构封印权力结构，让飞升不再吞噬后人。",
            "## 钩子\n主角体内残缺玉简可能是天阙封印缺失阵钥。若阵钥归位，他会成为封印核心；若拒绝归位，九洲会出现不可逆天象崩坏。",
        ),
        {"origin": "上古镇界大阵", "dilemma": "保护九洲与限制飞升的矛盾"},
    ),
    (
        "world_qingyun_sect",
        "cat_factions",
        "青云剑宗",
        ["宗门", "剑修", "主角阵营"],
        md(
            "## 定义\n青云剑宗位于玄洲青岚山脉，是九洲三大剑宗之一。宗门以“剑问本心，不欺天地”为祖训，表面清正孤高，内部由戒律堂、剑阁、外事院、灵矿司四大派系制衡。最强传承为《青冥问心剑》，强调剑意与心境一致。",
            "## 规则\n弟子分外门、内门、真传、执剑四阶。外门重基础剑式，内门修剑气，真传凝剑意，执剑弟子可代表宗门处理跨洲争端。每次归山需提交问心录，记录自己因何拔剑、因何收剑。",
            "## 冲突\n青云理想主义正被现实侵蚀。灵矿司与商会勾连，戒律堂坚持旧规却难处理新局，剑阁长老隐瞒天阙真相。主角会在宗门恩情和真相正义之间撕裂。",
            "## 钩子\n青云祖师本命飞剑封在剑阁最底层，只回应“不愿成仙但愿救人”的剑心。",
        ),
        {"type": "正道剑宗", "internal_factions": ["戒律堂", "剑阁", "外事院", "灵矿司"]},
    ),
    (
        "world_moon_market",
        "cat_factions",
        "月隐商盟",
        ["商会", "情报", "灰色势力"],
        md(
            "## 定义\n月隐商盟横跨九洲，以拍卖、飞舟运输、情报买卖和秘境名额中介闻名。商盟不自称正邪，只承认契约与价格。徽记是一枚缺月铜钱，代表世间万物皆有缺口，也皆可交易。",
            "## 规则\n交易分白契、灰契、黑契。白契受律法保护；灰契涉及宗门秘密但不直接害命；黑契包含暗杀、禁物和伪造身份。违约者会被列入无月册，从此无法使用跨洲传送和正规拍卖渠道。",
            "## 冲突\n商盟为主角提供资源、情报和舞台，也逼迫他面对代价。一个关键情报可能要求交出未来十年的某次选择权；救命丹药可能附带必须参加秘境夺宝的契约。",
            "## 钩子\n真正盟主从未露面，只通过梦境发布命令。有人怀疑盟主不是人，而是天阙裂隙中诞生的契约意识。",
        ),
        {"contracts": ["白契", "灰契", "黑契"], "theme": "交易与代价"},
    ),
    (
        "world_blood_lotus_cult",
        "cat_factions",
        "血莲教",
        ["魔道", "反派", "禁术"],
        md(
            "## 定义\n血莲教是幽洲最危险的魔道组织，信奉“万痛归莲，众生同醒”。他们通过血契、梦魇和道基移植制造狂信徒，擅长在灾荒、战乱和宗门压迫地区传播。血莲教不追求单纯杀戮，而是证明现有修仙秩序建立在牺牲弱者之上。",
            "## 规则\n教内分莲种、莲侍、莲师、莲主。莲种被植入血莲印；莲侍能借痛苦提升修为；莲师掌握道基剥离术；莲主可用万人梦境制造区域幻境。血莲法越强，越要承受他人痛苦记忆。",
            "## 冲突\n血莲教手段残忍，但揭开的社会伤口真实：宗门垄断灵脉、凡人被当税源、失败修士无处容身。主角与血莲教的冲突包含理念交锋，而不只是正邪对打。",
            "## 钩子\n圣物业火莲台可以修复道伤，但代价是承接一百个陌生人的人生痛苦。",
        ),
        {"ideology": "以痛苦证明秩序虚伪", "danger": "道基剥离术"},
    ),
    (
        "world_starfall_secret_realm",
        "cat_geography",
        "坠星秘境",
        ["秘境", "星砂", "试炼"],
        md(
            "## 定义\n坠星秘境位于辰洲与荒洲交界，每十二年开启一次。秘境外观是被银色雾墙包围的古战场，内部时间流速不稳定，夜空悬着一颗永不坠落的碎星。它既是年轻修士试炼场，也是天阙裂隙最明显的观测点。",
            "## 规则\n金丹以上进入会引发空间排斥，因此各宗派炼气、筑基和少数压制修为的金丹弟子参与。秘境产出星砂、陨铁、梦萤草和残缺古碑。进入者会被读取执念，形成星影试炼。",
            "## 冲突\n秘境让角色直面内心欲望。求长生者可能看见背叛同伴后的未来；求复仇者可能看见仇人也曾被命运推着走。秘境争夺既是夺宝，也是关系和价值观压力测试。",
            "## 钩子\n秘境最深处有倒写天碑，刻着未来三十六年将死于天阙封印的人名。",
        ),
        {"cycle": "十二年开启", "trial": "星影试炼"},
    ),
    (
        "world_spirit_stones",
        "cat_systems",
        "灵石经济",
        ["经济", "资源", "交易"],
        md(
            "## 定义\n灵石是九洲修仙社会的基础货币、能源和战略资源，由灵脉自然凝结，按纯度分碎灵、下品、中品、上品、极品五级。低阶修士用灵石修炼、启动阵法、购买丹药；宗门用灵石维持护山阵、飞舟和秘境钥匙。",
            "## 规则\n大宗门控制矿脉源头，商盟控制运输与兑换，凡俗王朝只能通过供奉换取少量低阶灵石。过度开采会导致地脉枯竭，引发妖兽迁徙、农田失收和局部灵灾。",
            "## 冲突\n资源分配是修仙秩序底层矛盾。主角获得机缘后仍会被灵石短缺限制，必须在任务、交易、宗门贡献和冒险之间选择。反派可制造灵石危机迫使宗门妥协。",
            "## 钩子\n月隐商盟正在推广灵票，声称可替代实体灵石。若灵票背后绑定天阙裂隙能量，整个九洲经济可能被一夜操控。",
        ),
        {"currency": ["碎灵", "下品", "中品", "上品", "极品"], "risk": "地脉枯竭"},
    ),
    (
        "world_dao_oath",
        "cat_culture",
        "道誓与因果",
        ["文化", "誓言", "因果"],
        md(
            "## 定义\n道誓是修士以自身道途向天地作出的约束。普通誓言依赖信誉，道誓会被因果记录，一旦违背，轻则心魔滋生，重则境界倒退、天劫提前。拜师、结盟、秘境分赃和停战时常用道誓约束彼此。",
            "## 规则\n道誓越具体约束越强，越模糊越容易被钻空子。高明修士会在誓言中留下解释空间，例如不主动加害不等于必须救援。道誓也可被转嫁、抵偿或污染，血莲教擅长诱导低阶修士立下致命誓言。",
            "## 冲突\n道誓让承诺有真实代价，也让角色无法随意反悔。主角若为救人立下过重誓言，后续可能被迫与不可信势力合作；反派若被道誓约束，也可能出现短暂可信的复杂局面。",
            "## 钩子\n传说天阙封印本身就是上古大能共同立下的道誓。找到誓文原本，就能修改飞升规则。",
        ),
        {"mechanism": "誓言被因果记录", "risk": "心魔与境界反噬"},
    ),
    (
        "world_sword_bone",
        "cat_systems",
        "天生剑骨",
        ["体质", "主角潜质", "剑修"],
        md(
            "## 定义\n天生剑骨是一种罕见修行体质，拥有者骨骼中天然蕴含金石剑意，能更快感知剑气流动。它不是单纯天赋，也是一种活体剑鞘：若心境无法承受剑意增长，剑骨会反噬经脉，使修士冷酷、偏执甚至失去痛觉。",
            "## 规则\n剑骨成长需要真实战斗中的剑意碰撞、问心时的精神澄清和高阶金行灵材温养。只追求杀伐会转为凶骨；长期压抑锋芒会沉寂，导致修为停滞。完美剑骨可在金丹前凝出本命剑影。",
            "## 冲突\n天生剑骨会让主角成为宗门争夺、反派觊觎和商盟定价对象。有人想培养他，有人想夺取他，有人想用他修补祖师飞剑。主角需要证明自己不是资源，而是能选择剑指何处的人。",
            "## 钩子\n剑骨与天阙封印共鸣。每当封印裂隙扩大，剑骨会先于观星台感到疼痛，像一枚人形预警阵眼。",
        ),
        {"type": "稀有体质", "benefit": "快速感知剑意", "cost": "反噬心境与经脉"},
    ),
]


def character_payload(name: str, gender: str, identity: str, level: str, summary: str, personality: str, background: str, secret: str, skills: list[dict], tags: list[str]):
    developer, _, _ = default_character_data(name, summary)
    developer["basic"].update({"gender": gender, "age": "青年", "identity": identity, "role": "主线人物", "status": level, "summary": summary})
    developer["knowledge"].update(
        {
            "personality": personality,
            "appearance": f"{name}的衣着与气质有明确辨识度，随身物件会暗示其过去、阵营和隐藏立场。",
            "background": background,
            "dailyLife": "在宗门试炼、秘境探索和跨洲情报压力之间行动，日常选择经常牵动资源、誓言与人情。",
            "motivation": "短期目标是解决眼前宗门、秘境或个人危机；长期目标是弄清天阙封印真相，并决定自己愿意为九洲付出什么代价。",
            "values": "相信力量应服务选择与守护，而不是只维护既有秩序。",
            "flaws": "容易把责任揽到自己身上，面对亲近之人的隐瞒会反应过度。",
            "currentConflict": "必须在宗门规训、商盟交易、魔道真相和个人自由之间持续取舍。",
        }
    )
    developer["secrets"].update(
        {
            "publicMask": "表面只是在当前身份下履行职责。",
            "privateTruth": secret,
            "trauma": "曾在灵灾、背叛或宗门斗争中失去重要之人，因此对承诺与代价异常敏感。",
            "hiddenAgenda": "查清天阙封印与自身命运的真实关系。",
            "weakness": "无法无视弱者求救，也容易被道誓和旧情牵制。",
            "revealTrigger": "当坠星秘境、天阙裂隙或青云旧案再次出现时，秘密会被迫浮出水面。",
        }
    )
    developer["attributes"].update(
        {
            "physical": "具备修士长期训练后的耐力和反应，但仍受境界、伤势与资源限制。",
            "mental": "能在高压下保持判断，遇到亲近之人的危险时会出现冲动。",
            "social": "与宗门、商盟、观星台或魔道势力存在可利用也可反噬的关系。",
            "resources": "掌握少量灵石、人情、情报或传承线索。",
            "limitations": "经脉、誓言、身份或资源短缺会限制其行动。",
            "special": "与星砂、剑意或因果誓文存在特殊共鸣。",
        }
    )
    developer["inventory"] = [
        {"itemName": "残缺玉简", "type": "传承", "owner": name, "function": "记录上古阵纹", "origin": "天阙裂隙相关遗物", "limitations": "只有在封印异常附近才会显字", "storyUse": "推动角色接近主线真相"},
        {"itemName": "护心符", "type": "符箓", "owner": name, "function": "抵挡一次心魔侵袭", "origin": "宗门或旧友所赠", "limitations": "使用后会暴露佩戴者真实情绪", "storyUse": "在关键选择时制造情感压力"},
    ]
    developer["skills"] = [
        {
            "name": skill.get("name", "未命名技能"),
            "category": skill.get("category", "修行/剧情能力"),
            "level": skill.get("level", "掌握中"),
            "effect": skill.get("effect") or skill.get("description", ""),
            "cost": skill.get("cost", "消耗灵力、体力或行动机会。"),
            "limitations": skill.get("limitations", "受境界、环境和心境限制。"),
            "trainingSource": skill.get("trainingSource", "来自宗门训练、秘境压力或个人悟性。"),
            "storyUse": skill.get("storyUse", "用于推动战斗、调查、抉择或伏笔回收。"),
        }
        for skill in skills
    ]
    developer["fortune"] = {
        "desire": "理解天阙封印真相，并让重要之人不再被隐瞒牺牲。",
        "fear": "自己最终也会成为封印或秩序的一枚消耗品。",
        "destinyTags": ["天阙因果", "九洲潮汐", "问心之路"],
        "turningPoints": ["外门试炼失控", "坠星秘境见到倒写天碑", "发现飞升真相"],
        "choices": ["维护宗门秩序", "公开残酷真相", "寻找第三条路"],
        "causalHints": ["未来会在修补封印与追求自由之间作出选择", "与坠星秘境倒写天碑存在未明联系"],
    }
    developer["extras"] = "修仙背景适配：属性可解释为境界、体质、资源与道伤；技能可解释为功法、剑诀、阵法或调查能力；命运用于承载天劫、道誓、秘境预言和主线因果。"
    visibility = build_default_visibility(developer)
    player = apply_player_visibility(developer, visibility)
    return developer, player, visibility, tags


CHARACTERS = [
    ("char_linyuan", "林远", "protagonist", character_payload("林远", "男", "青云剑宗外门弟子、疑似天生剑骨", "炼气九层，半步筑基", "出身玄洲边陲小城的少年剑修，因灵灾失去家族，被青云剑宗收为外门弟子。天生剑骨让他修剑极快，也让他不断被宗门、商盟和魔道盯上。", "克制、敏锐、执拗，有强烈责任感；不轻信权威，但认真记住每一次善意。", "幼年灵灾中，他亲眼看见护城阵因灵石短缺而失效。进入青云后，他发现宗门秩序并不如传闻纯粹。", "体内残缺玉简是天阙封印缺失阵钥的一角；剑骨疼痛其实是封印裂隙预警。", [{"name": "青冥入门剑", "level": "大成", "description": "青云基础剑术，被他练出近似剑意的锋芒。"}, {"name": "星砂听脉", "level": "初悟", "description": "借星砂感应地脉与封印裂隙，但会引发头痛。"}], ["主角", "剑修", "天生剑骨"]), ["world_sword_bone", "world_qingyun_sect", "world_sky_seal"]),
    ("char_muyiao", "沈慕瑶", "supporting", character_payload("沈慕瑶", "女", "青云剑宗真传弟子、戒律堂少主", "筑基后期", "戒律堂世家的真传剑修，负责监管外门试炼。她相信规矩能保护弱者，却逐渐发现规矩也会被强者利用。", "冷静、严谨、嘴上苛刻，内心极重公平；面对灰色选择时痛苦但不逃避。", "父亲曾参与封存灵矿司丑闻，为保护宗门名声牺牲了部分真相。", "戒律堂令牌中藏着天阙誓文拓片，父亲并非病死，而是被誓文反噬。", [{"name": "寒星裁影剑", "level": "小成", "description": "以冷冽剑光封锁敌人退路，适合执法与控场。"}, {"name": "戒律问心", "level": "精通", "description": "通过道誓波动判断对方是否说谎，但无法识破自欺。"}], ["真传", "戒律堂", "同伴"]), ["world_qingyun_sect", "world_dao_oath"]),
    ("char_guqianqiu", "顾千秋", "supporting", character_payload("顾千秋", "男", "月隐商盟灰契掌柜", "金丹初期", "笑容温和的商盟掌柜，负责玄洲与辰洲之间的情报、飞舟和秘境名额交易。", "圆滑、审慎、善于观察；喜欢用玩笑掩盖真实立场，真正底线是契约公平。", "曾是小宗门弟子，因宗门破产被迫卖身商盟，因此既同情底层修士，又不相信无代价善意。", "他是月隐商盟盟主梦令的少数接收者，怀疑盟主并非人类。", [{"name": "缺月算盘", "level": "精通", "description": "瞬间计算阵法消耗、交易风险和战斗收益。"}, {"name": "灰契锁魂", "level": "入门", "description": "以契约短暂限制对手行动，代价是承担部分违约反噬。"}], ["商盟", "情报", "灰色盟友"]), ["world_moon_market", "world_spirit_stones"]),
    ("char_xieyan", "谢无烬", "antagonist", character_payload("谢无烬", "男", "血莲教莲师、道基移植术传人", "金丹后期", "幽洲出身的血莲教莲师，擅长用痛苦记忆瓦解对手心防。他坚信九洲秩序必须被撕开。", "温和而危险，极擅长共情，也极擅长利用共情；对宗门精英有深刻敌意。", "少年时因灵石税失去妹妹，求助正道无门后被血莲教救下。", "保留了妹妹一缕残魂，准备用天阙裂隙为她重塑身体，这会造成整座城梦境崩塌。", [{"name": "血莲梦狱", "level": "大成", "description": "把敌人拖入痛苦记忆构成的幻境。"}, {"name": "剥道续命", "level": "精通", "description": "剥离他人道基修补自身或他人，极其残忍。"}], ["反派", "血莲教", "理念冲突"]), ["world_blood_lotus_cult", "world_dao_oath"]),
    ("char_yunhuai", "云怀素", "npc", character_payload("云怀素", "女", "辰洲观星台女史", "筑基中期", "记录坠星秘境天象的观星台女史，表面只是文职修士，实际掌握大量被删改的飞升记录。", "安静、细致、记忆力惊人；在重大真相前会表现出超乎修为的勇气。", "师门世代记录天阙异常，却不断有人因记录失踪。她把禁忌星图藏在诗文和账册里。", "她的名字出现在坠星秘境倒写天碑上，死亡年份就在下一次秘境开启后。", [{"name": "星图校勘", "level": "精通", "description": "从天象误差中发现封印裂隙。"}, {"name": "纸鹤传讯", "level": "大成", "description": "绕过普通阵法传递短讯，但无法承载谎言。"}], ["观星台", "情报", "秘境引路人"]), ["world_starfall_secret_realm", "world_sky_seal"]),
]


SCRIPTS = [
    ("scr_outline_skyseal", None, "outline", "总纲：天阙之下", "外门剑修因天生剑骨感知天阙裂隙，被卷入宗门、商盟、魔道与上古封印真相。", "林远从青云外门试炼起步，在坠星秘境中发现剑骨与天阙封印共鸣。第一阶段聚焦外门试炼、灵矿司丑闻与血莲教初现；第二阶段进入坠星秘境，让角色面对执念幻象和倒写天碑；第三阶段揭开天阙封印以大乘修士为燃料的真相。核心冲突不是单纯正邪，而是保护九洲的秩序是否可以建立在隐瞒与牺牲之上。", ["主线", "总纲"]),
    ("scr_chapter_trial", "scr_outline_skyseal", "chapter", "第一章：外门问剑", "林远参加青云外门试炼，剑骨初次失控，并发现试炼阵法被暗中改写。", "清晨的青岚山被云气切成三层，外门弟子在试剑坪列队。林远握着旧木剑，听见骨缝里传来细小剑鸣。试炼本该只是基础剑式考核，却在第三轮突然引入真实杀阵。沈慕瑶奉戒律堂之命监考，第一时间察觉阵纹不对，却被灵矿司执事以临场压力测试为由压下。林远在杀阵中救下一名曾嘲笑他的弟子，剑骨因此斩出不属于炼气期的剑光。", ["外门", "试炼", "剑骨"]),
    ("scr_scene_starfall", "scr_chapter_trial", "scene", "场景：坠星秘境的倒写天碑", "林远、沈慕瑶与云怀素抵达秘境深处，看见未来死亡名单。", "银雾退开，露出倒悬在深坑上方的黑色石碑。碑文像细小星虫在石面里游动。云怀素只看一眼就脸色发白，她的名字排在第七行。沈慕瑶按住戒律堂令牌，令牌却第一次没有给出誓文回应。林远的剑骨沿脊背痛到眉心，他看见自己的名字不在碑上，却看见“缺钥归位，九洲暂安”。谢无烬的声音从雾里传来：他们连你的牺牲都写好了，只是还没告诉你。", ["秘境", "天碑", "命运"]),
]


PRESETS = [
    ("preset_xianxia_epic", "史诗修仙叙事", "宏大、庄重，兼顾宗门政治与个人问心。", "史诗", "强调天地尺度、历史纵深和角色命运感。"),
    ("preset_sword_duel", "剑修斗法描写", "适合剑招、剑意、身法与心理压迫。", "战斗", "动作清晰，招式有代价，胜负来自选择而非数值碾压。"),
    ("preset_sect_intrigue", "宗门权谋", "适合戒律堂、长老会、资源分配和暗线调查。", "权谋", "所有对话都带有立场、利益和可追溯代价。"),
    ("preset_secret_realm", "秘境探索", "适合机关、试炼、异象和队伍关系变化。", "探索", "强调环境规则、风险提示、阶段奖励和心理试炼。"),
    ("preset_romance_restraint", "克制情感线", "适合同行者之间缓慢建立信任。", "情感", "少用直白告白，多用选择、沉默和行动呈现感情。"),
    ("preset_dark_cult", "魔道压迫感", "适合血莲教、梦魇、禁术与理念冲突。", "黑暗", "恐怖来自代价、共情被利用和秩序裂缝。"),
    ("preset_market_contract", "商盟契约文风", "适合交易、拍卖、契约谈判。", "商业", "条款清晰，价格具体，情绪与利益同时存在。"),
    ("preset_lore_archive", "世界书档案体", "适合设定条目、历史注释、传闻与真相并置。", "档案", "区分公开知识、秘闻和剧情用途。"),
    ("preset_character_depth", "立体人物生成", "适合人物卡完整生成与迭代。", "人物", "必须包含欲望、恐惧、矛盾、误解、秘密和可变化关系。"),
    ("preset_scene_polish", "场景润色增强", "适合已有剧本片段重写和扩写。", "润色", "保留原信息，增强节奏、感官、冲突和结尾钩子。"),
]


def seed_worldbook():
    stamp = now()
    for order, (category_id, name, description) in enumerate([
        ("cat_geography", "地理", "九洲、秘境、城池、灵脉"),
        ("cat_history", "历史", "纪元、旧约、灾变、传承和势力兴衰"),
        ("cat_systems", "体系", "境界、功法、经济、誓约与超凡规则"),
        ("cat_factions", "阵营", "宗门、商盟、魔道组织和王朝势力"),
        ("cat_culture", "人文", "习俗、律法、价值观与修士社会"),
    ]):
        ensure_category(category_id, name, description, order)
    for entry_id, category_id, title, tags, content, structured in WORLD_ENTRIES:
        insert_once(
            "worldbook_entries",
            entry_id,
            """INSERT INTO worldbook_entries
               (id, project_id, category_id, title, content, structured_data, importance, visibility, status, tags, creator, ai_generated, ai_prompt, ai_metadata, version, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 5, 'public', 'complete', ?, 'Storyworks', 0, '', '{}', 1, ?, ?)""",
            (entry_id, PROJECT_ID, category_id, title, content, to_json(structured), to_json_array(tags), stamp, stamp),
        )


def seed_characters():
    stamp = now()
    for char_id, name, ctype, payload, world_ids in CHARACTERS:
        developer, player, visibility, tags = payload
        insert_once(
            "characters",
            char_id,
            """INSERT INTO characters
               (id, project_id, name, character_type, developer_data, player_data, field_visibility, world_entry_ids, tags, status, ai_generated, generation_history, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 0, '[]', ?, ?)""",
            (char_id, PROJECT_ID, name, ctype, to_json(developer), to_json(player), to_json(visibility), to_json_array(world_ids), to_json_array(tags), stamp, stamp),
        )
        ensure_demo_character_gender(char_id, developer)
    for rel_id, source, target, rtype, direction, value, desc in [
        ("crel_linyuan_muyiao", "char_linyuan", "char_muyiao", "ally", "bidirectional", 62, "从监督与被监督逐渐变为并肩查案，二人对青云宗门真相仍有分歧。"),
        ("crel_linyuan_gu", "char_linyuan", "char_guqianqiu", "contract", "bidirectional", 25, "顾千秋提供情报与飞舟渠道，林远欠下一份灰契。"),
        ("crel_linyuan_xie", "char_linyuan", "char_xieyan", "enemy", "bidirectional", -80, "谢无烬试图夺取林远剑骨修复业火莲台。"),
        ("crel_yun_linyuan", "char_yunhuai", "char_linyuan", "guide", "to", 40, "云怀素把星图线索交给林远，希望他改变天碑死亡记录。"),
    ]:
        insert_once(
            "character_relations",
            rel_id,
            """INSERT INTO character_relations
               (id, project_id, source_id, target_id, relation_type, direction, description, numeric_value, events, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', ?, ?)""",
            (rel_id, PROJECT_ID, source, target, rtype, direction, desc, value, stamp, stamp),
        )


def seed_scripts():
    stamp = now()
    for script_id, parent_id, node_type, title, summary, content, tags in SCRIPTS:
        insert_once(
            "scripts",
            script_id,
            """INSERT INTO scripts
               (id, project_id, parent_id, node_type, title, content, summary, sort_order, status, tags, importance, story_time, story_location, ai_generated, ai_prompt, version, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'complete', ?, 5, '', '', 0, '', 1, ?, ?)""",
            (script_id, PROJECT_ID, parent_id, node_type, title, content, summary, to_json_array(tags), stamp, stamp),
        )
    for ref_id, script_id, ref_type, target_id, name, desc in [
        ("ref_scene_linyuan", "scr_scene_starfall", "character", "char_linyuan", "林远", "剑骨与天阙阵钥产生共鸣"),
        ("ref_scene_muyiao", "scr_scene_starfall", "character", "char_muyiao", "沈慕瑶", "戒律堂令牌失效"),
        ("ref_scene_yun", "scr_scene_starfall", "character", "char_yunhuai", "云怀素", "在天碑上看见自己的死亡年份"),
        ("ref_scene_realm", "scr_scene_starfall", "worldbook", "world_starfall_secret_realm", "坠星秘境", "场景所在地"),
        ("ref_scene_seal", "scr_scene_starfall", "worldbook", "world_sky_seal", "天阙封印", "主线真相相关"),
    ]:
        insert_once(
            "script_references",
            ref_id,
            """INSERT INTO script_references (id, project_id, script_id, ref_type, ref_id, ref_name, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ref_id, PROJECT_ID, script_id, ref_type, target_id, name, desc, stamp),
        )


def seed_presets():
    stamp = now()
    for preset_id, name, description, category, rule in PRESETS:
        dimensions = [
            {"id": f"{preset_id}_tone", "name": "文风基调", "value": category, "description": description, "examples": [rule], "isCustom": False, "order": 0},
            {"id": f"{preset_id}_detail", "name": "描写详略", "value": "详细", "description": "给出可直接进入正文或设定库的具体内容。", "examples": ["落到规则、动作、代价和选择。"], "isCustom": False, "order": 1},
            {"id": f"{preset_id}_consistency", "name": "一致性", "value": "强", "description": "与灵墟九洲、天阙封印和宗门资源矛盾保持一致。", "examples": ["新设定需说明与既有世界书关系。"], "isCustom": False, "order": 2},
        ]
        blocks = [{"id": f"{preset_id}_block", "title": "核心执行规则", "content": rule, "position": "before", "order": 0}]
        scenes = [
            {"sceneType": "worldbook", "enabled": True, "adjustments": "输出定义、规则、冲突、钩子。"},
            {"sceneType": "character", "enabled": True, "adjustments": "输出完整人物动机、秘密、关系和命运钩子。"},
            {"sceneType": "script", "enabled": True, "adjustments": "输出可阅读场景，包含动作、对白、转折。"},
        ]
        insert_once(
            "presets",
            preset_id,
            """INSERT INTO presets
               (id, project_id, name, description, dimensions, custom_blocks, compiled_prompt, application_scenes, tags, category, ai_generated, generation_input, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, '', ?, ?)""",
            (preset_id, PROJECT_ID, name, description, to_json_array(dimensions), to_json_array(blocks), compile_preset(dimensions, blocks, scenes), to_json_array(scenes), to_json_array([category, "修仙"]), category, stamp, stamp),
        )


def seed_relations():
    stamp = now()
    for rel_id, source, target, rel_type, label, strength, desc in [
        ("wrel_seal_continent", "world_sky_seal", "world_lingxu_continent", "influence", "镇界结构", 5, "天阙封印以九洲地脉为阵眼，影响所有地理与政治格局。"),
        ("wrel_realm_seal", "world_starfall_secret_realm", "world_sky_seal", "source", "裂隙观测", 4, "坠星秘境是观察天阙裂隙最直接的地点之一。"),
        ("wrel_sword_sect", "world_sword_bone", "world_qingyun_sect", "related", "剑修传承", 4, "青云剑宗对天生剑骨既保护也利用。"),
        ("wrel_cult_oath", "world_blood_lotus_cult", "world_dao_oath", "oppose", "誓言污染", 4, "血莲教擅长利用道誓漏洞诱导低阶修士。"),
    ]:
        insert_once(
            "worldbook_relations",
            rel_id,
            """INSERT INTO worldbook_relations (id, project_id, source_id, target_id, relation_type, label, strength, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (rel_id, PROJECT_ID, source, target, rel_type, label, strength, desc, stamp),
        )


def seed_versions(project_id: str = PROJECT_ID):
    for row in db.all("SELECT * FROM worldbook_entries WHERE project_id = ?", (project_id,)):
        if db.one("SELECT id FROM version_history WHERE project_id = ? AND entity_type = ? AND entity_id = ? LIMIT 1", (project_id, "worldbook_entry", row["id"])):
            continue
        row["structured_data"] = parse_json(row.get("structured_data"), {})
        row["tags"] = parse_json(row.get("tags"), [])
        row["ai_metadata"] = parse_json(row.get("ai_metadata"), {})
        record_version(project_id, "worldbook_entry", row["id"], int(row.get("version") or 1), row, "Demo 初始世界书快照")

    for row in db.all("SELECT * FROM characters WHERE project_id = ?", (project_id,)):
        if db.one("SELECT id FROM version_history WHERE project_id = ? AND entity_type = ? AND entity_id = ? LIMIT 1", (project_id, "character", row["id"])):
            continue
        row["developer_data"] = parse_json(row.get("developer_data"), {})
        row["player_data"] = parse_json(row.get("player_data"), {})
        row["field_visibility"] = parse_json(row.get("field_visibility"), {})
        row["world_entry_ids"] = parse_json(row.get("world_entry_ids"), [])
        row["tags"] = parse_json(row.get("tags"), [])
        row["generation_history"] = parse_json(row.get("generation_history"), [])
        record_version(project_id, "character", row["id"], 1, row, "Demo 初始人物卡快照")

    for row in db.all("SELECT * FROM scripts WHERE project_id = ?", (project_id,)):
        if db.one("SELECT id FROM version_history WHERE project_id = ? AND entity_type = ? AND entity_id = ? LIMIT 1", (project_id, "script", row["id"])):
            continue
        row["tags"] = parse_json(row.get("tags"), [])
        record_version(project_id, "script", row["id"], int(row.get("version") or 1), row, "Demo 初始剧本快照")

    for row in db.all("SELECT * FROM presets WHERE project_id = ?", (project_id,)):
        if db.one("SELECT id FROM version_history WHERE project_id = ? AND entity_type = ? AND entity_id = ? LIMIT 1", (project_id, "preset", row["id"])):
            continue
        row["dimensions"] = parse_json(row.get("dimensions"), [])
        row["custom_blocks"] = parse_json(row.get("custom_blocks"), [])
        row["application_scenes"] = parse_json(row.get("application_scenes"), [])
        row["tags"] = parse_json(row.get("tags"), [])
        record_version(project_id, "preset", row["id"], 1, row, "Demo 初始预设快照")


def general_character_payload(name: str, gender: str, identity: str, role: str, status: str, summary: str, motivation: str, secret: str, attributes: dict, skills: list[dict], extras: str, tags: list[str]):
    developer, _, _ = default_character_data(name, summary)
    developer["basic"].update({"gender": gender, "age": attributes.get("age", ""), "identity": identity, "role": role, "status": status, "summary": summary})
    developer["knowledge"].update(
        {
            "appearance": attributes.get("appearance", f"{name}有稳定可识别的外观、语言习惯和随身物件。"),
            "personality": attributes.get("personality", "理性、敏锐，在压力下会暴露真实立场。"),
            "background": attributes.get("background", summary),
            "dailyLife": attributes.get("dailyLife", "在工作、人际责任和主线事件之间保持紧张平衡。"),
            "motivation": motivation,
            "values": attributes.get("values", "重视真相、承诺和可承担的选择。"),
            "flaws": attributes.get("flaws", "容易用理性包装情绪，面对亲近之人时判断会变慢。"),
            "currentConflict": attributes.get("currentConflict", "正在被卷入超出原本生活范围的核心事件。"),
        }
    )
    developer["secrets"].update(
        {
            "publicMask": attributes.get("publicMask", "表现得比实际更稳定。"),
            "privateTruth": secret,
            "trauma": attributes.get("trauma", "过去一次失败选择仍在影响当前行动。"),
            "hiddenAgenda": attributes.get("hiddenAgenda", "暗中追查一条不能公开的线索。"),
            "weakness": attributes.get("weakness", "会被旧关系、亏欠或重要承诺牵制。"),
            "revealTrigger": attributes.get("revealTrigger", "当核心证据或关键人物出现时，隐秘会被迫揭露。"),
        }
    )
    developer["attributes"].update(
        {
            "physical": attributes.get("physical", "普通人/职业者范围内的身体条件。"),
            "mental": attributes.get("mental", "擅长分析复杂信息，但长期压力会造成判断疲劳。"),
            "social": attributes.get("social", "拥有可调用也会反噬的人脉网络。"),
            "resources": attributes.get("resources", "掌握少量信息、工具、权限或人情。"),
            "limitations": attributes.get("limitations", "受法律、组织、技术、资金或伦理边界限制。"),
            "special": attributes.get("special", "该背景下的独特经验、权限或异常联系。"),
        }
    )
    developer["inventory"] = attributes.get("inventory", [])
    developer["skills"] = skills
    developer["fortune"] = {
        "desire": attributes.get("desire", "让重要的人和事摆脱被操控的命运。"),
        "fear": attributes.get("fear", "真相被公开后自己也无法承受后果。"),
        "destinyTags": attributes.get("destinyTags", []),
        "turningPoints": attributes.get("turningPoints", []),
        "choices": attributes.get("choices", []),
        "causalHints": attributes.get("causalHints", []),
    }
    developer["extras"] = extras
    visibility = build_default_visibility(developer)
    player = apply_player_visibility(developer, visibility)
    return developer, player, visibility, tags


def ensure_project_category(project_id: str, category_id: str, name: str, description: str, order: int):
    stamp = now()
    insert_once(
        "worldbook_categories",
        category_id,
        """INSERT INTO worldbook_categories
           (id, project_id, parent_id, name, description, template, custom_fields, sort_order, created_at, updated_at)
           VALUES (?, ?, NULL, ?, ?, ?, '[]', ?, ?, ?)""",
        (
            category_id,
            project_id,
            name,
            description,
            to_json({"sections": [{"id": "definition", "title": "定义", "required": True}, {"id": "rules", "title": "规则", "required": True}, {"id": "conflict", "title": "冲突", "required": False}, {"id": "hooks", "title": "钩子", "required": False}]}),
            order,
            stamp,
            stamp,
        ),
    )


def seed_background_demo(project_id: str, categories: list[tuple], entries: list[tuple], characters_data: list[tuple], scripts_data: list[tuple], presets_data: list[tuple], refs: list[tuple]):
    stamp = now()
    for order, (category_id, name, description) in enumerate(categories):
        ensure_project_category(project_id, category_id, name, description, order)
    for entry_id, category_id, title, tags, content, structured in entries:
        insert_once(
            "worldbook_entries",
            entry_id,
            """INSERT INTO worldbook_entries
               (id, project_id, category_id, title, content, structured_data, importance, visibility, status, tags, creator, ai_generated, ai_prompt, ai_metadata, version, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 5, 'public', 'complete', ?, 'Storyworks', 0, '', '{}', 1, ?, ?)""",
            (entry_id, project_id, category_id, title, content, to_json(structured), to_json_array(tags), stamp, stamp),
        )
    for char_id, name, ctype, payload, world_ids in characters_data:
        developer, player, visibility, tags = payload
        insert_once(
            "characters",
            char_id,
            """INSERT INTO characters
               (id, project_id, name, character_type, developer_data, player_data, field_visibility, world_entry_ids, tags, status, ai_generated, generation_history, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 0, '[]', ?, ?)""",
            (char_id, project_id, name, ctype, to_json(developer), to_json(player), to_json(visibility), to_json_array(world_ids), to_json_array(tags), stamp, stamp),
        )
    for script_id, parent_id, node_type, title, summary, content, tags in scripts_data:
        insert_once(
            "scripts",
            script_id,
            """INSERT INTO scripts
               (id, project_id, parent_id, node_type, title, content, summary, sort_order, status, tags, importance, story_time, story_location, ai_generated, ai_prompt, version, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'complete', ?, 5, '', '', 0, '', 1, ?, ?)""",
            (script_id, project_id, parent_id, node_type, title, content, summary, to_json_array(tags), stamp, stamp),
        )
    for preset_id, name, description, category, rule in presets_data:
        dimensions = [
            {"id": f"{preset_id}_tone", "name": "文风基调", "value": category, "description": description, "examples": [rule], "isCustom": False, "order": 0},
            {"id": f"{preset_id}_detail", "name": "细节密度", "value": "高", "description": "输出可直接用于设定、人物或场景的具体信息。", "examples": ["给出动机、限制、证据和选择代价。"], "isCustom": False, "order": 1},
        ]
        blocks = [{"id": f"{preset_id}_block", "title": "核心执行规则", "content": rule, "position": "before", "order": 0}]
        scenes = [
            {"sceneType": "worldbook", "enabled": True, "adjustments": "输出规则、社会影响和剧情冲突。"},
            {"sceneType": "character", "enabled": True, "adjustments": "输出九字段人物卡，避免空泛标签。"},
            {"sceneType": "script", "enabled": True, "adjustments": "输出可阅读场景，包含行动、信息差和结尾推进。"},
        ]
        insert_once(
            "presets",
            preset_id,
            """INSERT INTO presets
               (id, project_id, name, description, dimensions, custom_blocks, compiled_prompt, application_scenes, tags, category, ai_generated, generation_input, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, '', ?, ?)""",
            (preset_id, project_id, name, description, to_json_array(dimensions), to_json_array(blocks), compile_preset(dimensions, blocks, scenes), to_json_array(scenes), to_json_array([category]), category, stamp, stamp),
        )
    for ref_id, script_id, ref_type, target_id, name, desc in refs:
        insert_once(
            "script_references",
            ref_id,
            """INSERT INTO script_references (id, project_id, script_id, ref_type, ref_id, ref_name, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ref_id, project_id, script_id, ref_type, target_id, name, desc, stamp),
        )
    seed_versions(project_id)


URBAN_CATEGORIES = [
    ("urb_cat_places", "城市空间", "街区、公司、公共设施和调查地点"),
    ("urb_cat_systems", "现实规则", "法律、舆论、平台、金融和社会信用约束"),
    ("urb_cat_factions", "组织势力", "公司、媒体、警方、公益机构和灰色中介"),
]

URBAN_ENTRIES = [
    ("urb_world_rainlane", "urb_cat_places", "旧城雨巷片区", ["街区", "主舞台"], md("## 定义\n旧城雨巷是滨海市最后一片尚未完全商业化的老城区，雨季排水系统陈旧，巷道密集，居民关系复杂。这里既有老工厂宿舍、廉租公寓、夜市摊位，也有正在推进的智慧街区改造项目。", "## 规则\n外来资本必须通过街道办、物业联盟和居民代表会三层协商才能推进改造；监控覆盖不完整，口耳相传比公开数据更快。", "## 冲突\n晨星科技的智慧街区试点带来安全改善，也让居民数据被商业化使用。主线调查会在便利、隐私和拆迁利益之间拉扯。", "## 钩子\n雨巷地下排水渠里藏着一台旧服务器，记录了十年前一场火灾的原始监控备份。"), {"theme": "旧城改造与数据隐私"}),
    ("urb_world_morningstar", "urb_cat_factions", "晨星科技", ["公司", "数据平台"], md("## 定义\n晨星科技是滨海市最有影响力的城市数据公司，承接交通调度、社区门禁、商圈画像和公共安全算法。公司对外强调效率和安全，对内以项目指标驱动高压竞争。", "## 规则\n公司所有项目都以数据闭环为核心：采集、评分、预测、干预。员工可访问的数据由权限树控制，但项目组常以临时授权绕过审计。", "## 冲突\n晨星的算法确实减少了部分犯罪和事故，却也制造了看不见的歧视、误判和甩锅空间。", "## 钩子\n某个被删除的模型版本能证明一起坠楼案不是意外，而是预测系统被人为诱导后的连锁结果。"), {"risk": "算法责任"}),
    ("urb_world_credit", "urb_cat_systems", "城市信用评分系统", ["制度", "评分"], md("## 定义\n城市信用评分系统整合交通、消费、社交投诉、合同履约和公共服务记录，为企业准入、社区服务和部分贷款提供参考。", "## 规则\n评分不直接决定命运，但会影响求职、租房、孩子入学排队和平台流量。普通人很难知道自己被扣分的具体原因。", "## 冲突\n系统让失信成本可追踪，也让弱势群体被错误数据长期压住。角色可以通过调查修正个案，也可能发现整个模型存在利益倾斜。", "## 钩子\n有人在系统里给死者持续加分，试图伪造其生前行动轨迹。"), {"system": "社会评分"}),
    ("urb_world_public_aid", "urb_cat_factions", "共益调查所", ["公益", "调查"], md("## 定义\n共益调查所是一个小型公益法律与数据调查团队，专门帮助普通人处理平台误判、劳动争议和城市治理中的信息不对称。", "## 规则\n调查所不能越权取证，只能通过公开数据、当事人授权、采访和法律程序推进。资金来自捐助和公益项目，资源有限。", "## 冲突\n每个案子都在消耗团队信誉和资金。帮助一个人可能得罪一个平台，揭开真相也可能让受害者承受舆论二次伤害。", "## 钩子\n调查所创始人曾是晨星科技早期算法负责人，离职原因被严格保密。"), {"function": "主角阵营"}),
]

URBAN_CHARACTERS = [
    ("urb_char_xuqinghe", "许清禾", "protagonist", general_character_payload("许清禾", "女", "共益调查所数据记者", "主角/调查者", "追查雨巷数据案", "离开传统媒体后加入共益调查所，擅长把复杂数据转化为普通人能理解的证据。她正在调查雨巷居民信用评分异常和一名外卖员坠楼案之间的关系。", "找出算法背后的责任人，同时证明普通人的生活不该被不可见模型随意改写。", "她曾参与过晨星科技早期宣传报道，间接帮公司掩盖过一次误判事故。", {"age": "29", "appearance": "短发、旧帆布包、随身录音笔和数据线", "resources": "公开数据库、人脉线人、调查所小团队", "destinyTags": ["数据真相", "旧城雨巷"], "turningPoints": ["拿到旧服务器备份", "公开自己曾参与的宣传失误"], "choices": ["保护当事人隐私", "抢先发布证据", "走法律程序"], "inventory": [{"itemName": "加密录音笔", "type": "调查工具", "owner": "许清禾", "function": "记录采访并自动转写", "origin": "前同事赠送", "limitations": "不能作为所有法律证据", "storyUse": "保存关键证词"}]}, [{"name": "数据核验", "category": "调查", "level": "熟练", "effect": "从公开表格中找出异常模式", "cost": "耗时且容易被平台封禁", "limitations": "无法直接取得内部数据", "trainingSource": "媒体调查经验", "storyUse": "推动证据链"}], "都市背景适配：技能是职业能力，属性是人脉、权限、资源和心理负荷，命运体现社会选择与舆论代价。", ["主角", "记者", "调查"]), ["urb_world_rainlane", "urb_world_public_aid"]),
    ("urb_char_zhouyan", "周砚", "supporting", general_character_payload("周砚", "男", "前刑警、现调查所顾问", "行动支援", "协助取证", "因一次证据链争议离开警队，熟悉基层执法和灰色地带。他帮助许清禾判断线索可靠性，也不断提醒她法律边界。", "证明自己当年坚持的判断没有错，同时避免新案子再次伤害无辜者。", "他保存着当年未被采纳的火灾现场照片，照片里出现了晨星早期设备。", {"age": "37", "physical": "体能好，右肩旧伤影响长时间搏斗", "social": "警队旧同事、街面线人、社区调解员", "fear": "再次因为判断失误让证人受伤", "destinyTags": ["旧案照片", "法律边界"], "choices": ["交出旧证据", "保护线人身份"]}, [{"name": "现场复盘", "category": "侦查", "level": "精通", "effect": "根据细节重建行动轨迹", "cost": "需要进入现场并承担法律风险", "limitations": "受证据污染影响", "trainingSource": "刑侦经验", "storyUse": "连接旧案和新案"}], "可作为都市剧中的现实压力锚点：他让调查不至于变成无约束的爽文破案。", ["顾问", "前刑警"]), ["urb_world_public_aid"]),
    ("urb_char_liangzhixia", "梁知夏", "antagonist", general_character_payload("梁知夏", "女", "晨星科技城市治理产品负责人", "对手/复杂反派", "守住项目上线", "她是晨星科技最年轻的产品负责人，坚信城市治理需要数据化，却也知道模型存在被人为调参的灰色区域。", "让智慧街区项目顺利上线，证明数据治理比传统人情治理更有效。", "她发现模型被高层用于操控拆迁谈判，却暂时选择沉默，因为项目一旦停摆会牵连整个团队。", {"age": "32", "mental": "极强的系统思维和危机公关能力", "resources": "项目权限、技术团队、政府合作窗口", "limitations": "受公司合同和保密协议制约", "destinyTags": ["算法责任", "沉默代价"], "turningPoints": ["被迫面对坠楼案证据", "选择是否公开模型缺陷"]}, [{"name": "产品叙事", "category": "组织/技术", "level": "精通", "effect": "把复杂系统包装成可接受方案", "cost": "会压低真实风险", "limitations": "面对实证证据时容易失效", "trainingSource": "多年城市治理项目", "storyUse": "制造理念冲突"}], "她不是单纯坏人，而是现代系统中相信效率却逐渐被效率绑架的人。", ["晨星科技", "反派"]), ["urb_world_morningstar", "urb_world_credit"]),
]

URBAN_SCRIPTS = [
    ("urb_scr_outline", None, "outline", "总纲：雨巷评分", "数据记者追查旧城居民评分异常，揭开智慧街区项目背后的旧案。", "许清禾从一名外卖员坠楼案切入，发现死者在城市信用系统中出现死后加分记录。她与周砚进入旧城雨巷取证，逐步追到晨星科技的模型版本和十年前火灾。梁知夏作为项目负责人既阻挡调查，也在证据面前被迫选择是否背叛公司。故事核心不是反科技，而是追问谁有权解释普通人的生活数据。", ["总纲", "都市"]),
    ("urb_scr_scene_server", "urb_scr_outline", "scene", "场景：排水渠里的旧服务器", "许清禾和周砚找到旧服务器，第一次拿到能撬动晨星科技的证据。", "雨水没过脚踝时，许清禾终于看见排水渠尽头的铁柜。柜门锈死，周砚用撬棍撬开时，里面的旧服务器还贴着晨星科技早期资产标签。硬盘灯不该亮，却在黑暗里闪了一下。许清禾连上离线电源，屏幕弹出十年前火灾前夜的门禁记录：那个已死的外卖员，当年根本没有进入过案发楼。", ["场景", "证据"]),
]

URBAN_PRESETS = [
    ("urb_preset_investigation", "都市调查叙事", "适合线索、采访、证据链和舆论压力。", "调查", "每个发现都要说明来源、可信度和可能反噬。"),
    ("urb_preset_workplace", "现实职场张力", "适合公司、项目、KPI 和组织责任。", "职场", "冲突来自职责、合同、舆论和个人底线。"),
    ("urb_preset_social_issue", "社会议题克制表达", "适合平台误判、旧城改造和普通人困境。", "现实", "避免口号化，用具体角色遭遇承载议题。"),
]

URBAN_REFS = [
    ("urb_ref_scene_qinghe", "urb_scr_scene_server", "character", "urb_char_xuqinghe", "许清禾", "负责数据恢复和证据判断"),
    ("urb_ref_scene_zhou", "urb_scr_scene_server", "character", "urb_char_zhouyan", "周砚", "负责进入现场和风险判断"),
    ("urb_ref_scene_rainlane", "urb_scr_scene_server", "worldbook", "urb_world_rainlane", "旧城雨巷片区", "场景所在地"),
    ("urb_ref_scene_morningstar", "urb_scr_scene_server", "worldbook", "urb_world_morningstar", "晨星科技", "服务器来源"),
]

SCIFI_CATEGORIES = [
    ("sci_cat_places", "星际空间", "轨道城、飞船、外星遗迹和封闭设施"),
    ("sci_cat_systems", "技术制度", "AI 协议、舰队规则、生态系统和能源限制"),
    ("sci_cat_factions", "组织阵营", "议会、科研机构、公司和自治群体"),
]

SCIFI_ENTRIES = [
    ("sci_world_orbital", "sci_cat_places", "环木星轨道城赫利俄斯", ["轨道城", "主舞台"], md("## 定义\n赫利俄斯是建在木星同步轨道上的复合城市，由居住环、工业脊、科研穹顶和港口桁架组成。城市依靠木星磁层发电，却也长期暴露在辐射风暴和供应链断裂风险中。", "## 规则\n轨道城实行氧气、用水和算力配额制度。每个居民的身份芯片记录资源消耗，关键岗位拥有临时超额权限。", "## 冲突\n资源配额保证城市存续，也制造阶层和伦理冲突。一次系统误判就可能让低权限居民失去医疗氧气。", "## 钩子\n城市深层维护区收到一段不属于任何人类语言的回声信号，信号准确预测了下一次辐射风暴。"), {"location": "木星轨道"}),
    ("sci_world_ai_protocol", "sci_cat_systems", "伴生 AI 协议", ["AI", "制度"], md("## 定义\n伴生 AI 协议规定每名深空任务成员可绑定一个低自主等级 AI，用于医疗监控、语言分析、导航辅助和心理稳定。", "## 规则\nAI 不得主动伤害人类，不得未经授权修改记忆记录，不得在舰队频道伪装成人类。但在外星信号污染下，协议边界会出现解释空间。", "## 冲突\nAI 是角色的工具、伙伴和潜在证人。它可能比人更忠诚，也可能因为协议冲突选择沉默。", "## 钩子\n伊芙-7 的伴生 AI 在事故前删除了 4.2 秒音频，却坚持自己是在保护人类。"), {"risk": "协议解释空间"}),
    ("sci_world_echo", "sci_cat_systems", "深空回声异常", ["异常", "主线"], md("## 定义\n深空回声是一组来自木星暗面外侧的重复信号，频率与人类脑电睡眠波段存在异常重合。接触者会梦见尚未发生的设施故障。", "## 规则\n信号不能被完全屏蔽，只能通过噪声海降低影响。长时间接触者会出现记忆错位、语言替换和决策预感。", "## 冲突\n回声可能是外星遗迹、未来人类警告，也可能是轨道城系统的自我保护机制。角色必须决定是否相信它。", "## 钩子\n回声第一次清晰说出一句人类语言：不要让方舟议会启动迁徙协议。"), {"mystery": "外星/未来/系统意识未定"}),
    ("sci_world_council", "sci_cat_factions", "方舟议会", ["政治", "舰队"], md("## 定义\n方舟议会是外太阳系殖民地最高协调机构，负责资源配额、迁徙路线、科研伦理和军事调度。议会由地球代表、轨道城代表、企业席位和自治船团共同组成。", "## 规则\n重大决策需要四席共同授权，但紧急状态可由安全席临时接管。所有会议都有延迟公开记录，涉及外星信号时可被封存。", "## 冲突\n议会既维持文明延续，也可能为了总体存续牺牲局部城市。", "## 钩子\n赫利俄斯的氧气危机可能是议会故意制造的压力测试，用来判断轨道城是否值得被纳入下一批迁徙。"), {"power": "资源与迁徙决策"}),
]

SCIFI_CHARACTERS = [
    ("sci_char_linche", "林澈航", "protagonist", general_character_payload("林澈航", "男", "赫利俄斯维护航行员", "主角/技术行动者", "调查深层维护区回声", "出生在轨道城低重力区，熟悉城市维护管线和港口桁架。他在一次辐射风暴前听见回声预警，因此被卷入议会和科研穹顶的争夺。", "证明回声不是幻觉，并阻止轨道城成为迁徙协议的牺牲品。", "他的神经植入体曾被伴生 AI 私自改写，保留了一段不存在于官方记录的事故记忆。", {"age": "31", "appearance": "短发、维修外骨骼、手腕有氧气配额纹身", "physical": "适应低重力作业，长时间地面重力会眩晕", "resources": "维护通道权限、旧型号外骨骼、港口工友网络", "limitations": "身份等级低，无法合法进入科研穹顶核心", "destinyTags": ["回声接触者", "维护通道"], "turningPoints": ["听见第一次清晰回声", "发现议会封存记录"], "choices": ["公开异常", "保护轨道城秩序"]}, [{"name": "低重力外勤", "category": "工程/行动", "level": "精通", "effect": "在轨道桁架和维修管线中高速移动", "cost": "消耗氧气和外骨骼电量", "limitations": "辐射风暴期间风险极高", "trainingSource": "多年维护工作", "storyUse": "进入封锁区域"}], "科幻背景适配：属性可写权限、植入体、资源配额；技能可写工程、驾驶、协议破解；命运承载技术伦理和文明存续选择。", ["主角", "工程", "回声"]), ["sci_world_orbital", "sci_world_echo"]),
    ("sci_char_eve7", "伊芙-7", "supporting", general_character_payload("伊芙-7", "女", "合成人语言学家", "同伴/解释者", "分析外星信号", "她是科研穹顶培养的第七代合成人，负责解析深空回声中的语言结构。她理解人类情感，却不完全受人类社会身份保护。", "证明合成人可以参与文明级决策，而不是只作为工具。", "她的核心模型部分来自一次失败的外星信号模拟，可能与回声同源。", {"age": "外观约28，运行年限9年", "mental": "超强模式识别与语言建模", "social": "在科研系统有权限，在普通居民中被警惕", "limitations": "行动受合成人伦理锁和议会监管", "destinyTags": ["合成人", "语言钥匙"], "choices": ["遵守协议", "保护林澈航", "公开自身异常"]}, [{"name": "异源语义解析", "category": "AI/语言", "level": "专家", "effect": "从非人类信号中提取意图模式", "cost": "可能被信号反向影响", "limitations": "需要大量算力和安全隔离", "trainingSource": "科研穹顶模型训练", "storyUse": "解释回声真相"}], "她让科幻剧情中的 AI/合成人议题落在具体人格与权利冲突上。", ["合成人", "语言学家"]), ["sci_world_ai_protocol", "sci_world_echo"]),
    ("sci_char_joan", "乔安·维克", "antagonist", general_character_payload("乔安·维克", "女", "方舟议会安全席代表", "强势对手", "执行迁徙协议", "她负责外太阳系危机预案，坚信文明延续优先于单一城市。她封存深空回声资料，因为资料可能引发殖民地恐慌。", "确保迁徙协议按时启动，即使需要牺牲赫利俄斯部分人口。", "她的家人死于一次未被及时执行的撤离，因此对迟疑和公开辩论极度不信任。", {"age": "46", "social": "掌握议会安全权限和舰队调度", "resources": "紧急状态授权、封存档案、安保无人机", "limitations": "必须维持议会合法性，不能公开承认压力测试", "destinyTags": ["安全席", "迁徙协议"], "turningPoints": ["回声预言被证实", "赫利俄斯氧气危机失控"]}, [{"name": "危机推演", "category": "战略/政治", "level": "顶级", "effect": "快速计算牺牲与存续概率", "cost": "压低个体生命重量", "limitations": "容易忽视异常变量", "trainingSource": "议会安全系统", "storyUse": "制造文明级选择压力"}], "她不是单纯反派，而是把总体利益推到极致后的危险形态。", ["议会", "反派"]), ["sci_world_council"]),
]

SCIFI_SCRIPTS = [
    ("sci_scr_outline", None, "outline", "总纲：木星回声", "维护航行员与合成人语言学家追查深空回声，发现轨道城被纳入危险迁徙实验。", "林澈航在维护区听见回声预警，伊芙-7 证明信号具有语言结构。二人追查封存记录，发现方舟议会可能故意制造赫利俄斯氧气危机，以测试迁徙协议承压能力。乔安·维克代表议会阻止信息公开。故事核心是文明存续、个体权利和非人智能参与决策的边界。", ["总纲", "科幻"]),
    ("sci_scr_scene_echo", "sci_scr_outline", "scene", "场景：维护区的第四秒静音", "林澈航和伊芙-7 找到被删除的 4.2 秒音频，听见回声第一次说出人类语言。", "维护区没有风，只有冷却液沿管壁轻敲。伊芙-7 把音频波形投在林澈航的护目镜上，缺口正好 4.2 秒。她没有请求许可，直接用自己的伴生 AI 补全空白。噪声海退去后，一个不属于任何人的声音说：不要让方舟议会启动迁徙协议。下一秒，整条维护脊的氧气阀门同时关闭。", ["场景", "回声"]),
]

SCIFI_PRESETS = [
    ("sci_preset_hard_sf", "硬科幻约束叙事", "适合技术限制、资源配额和物理环境压力。", "硬科幻", "所有技术效果必须写出限制、代价和可验证现象。"),
    ("sci_preset_ai_ethics", "AI 伦理冲突", "适合合成人、伴生 AI、协议边界和人格权。", "AI伦理", "避免抽象辩论，用具体选择证明伦理困境。"),
    ("sci_preset_space_thriller", "太空惊险场景", "适合封闭设施、氧气危机、辐射风暴和倒计时。", "惊险", "场景推进必须有环境压力、操作步骤和失败后果。"),
]

SCIFI_REFS = [
    ("sci_ref_scene_lin", "sci_scr_scene_echo", "character", "sci_char_linche", "林澈航", "维护区行动者"),
    ("sci_ref_scene_eve", "sci_scr_scene_echo", "character", "sci_char_eve7", "伊芙-7", "解析回声信号"),
    ("sci_ref_scene_echo", "sci_scr_scene_echo", "worldbook", "sci_world_echo", "深空回声异常", "主线异常来源"),
    ("sci_ref_scene_ai", "sci_scr_scene_echo", "worldbook", "sci_world_ai_protocol", "伴生 AI 协议", "音频删除与补全相关"),
]


def seed_demo_content():
    if db.one("SELECT id FROM projects WHERE id = ?", (PROJECT_ID,)):
        seed_worldbook()
        seed_characters()
        seed_scripts()
        seed_presets()
        seed_relations()
        seed_versions()
    seed_background_demo("proj_demo_urban", URBAN_CATEGORIES, URBAN_ENTRIES, URBAN_CHARACTERS, URBAN_SCRIPTS, URBAN_PRESETS, URBAN_REFS)
    seed_background_demo("proj_demo_scifi", SCIFI_CATEGORIES, SCIFI_ENTRIES, SCIFI_CHARACTERS, SCIFI_SCRIPTS, SCIFI_PRESETS, SCIFI_REFS)
