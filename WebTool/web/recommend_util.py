import heapq
from keras.layers import Embedding, Flatten, Multiply, Dense, Input
from keras.models import Model
import keras

keras.backend.clear_session()
import numpy as np
import random


def get_recommend_model(num_users, num_items, latent_dim=8):
    """
    获得NCF模型定义
    :param num_users:
    :param num_items:
    :param latent_dim:
    :return:
    """
    user_input = Input(shape=(1,), dtype='int32', name='user_input')
    item_input = Input(shape=(1,), dtype='int32', name='item_input')
    MF_Embedding_User = Embedding(input_dim=num_users, output_dim=latent_dim, name='user_embedding', input_length=1)
    MF_Embedding_Item = Embedding(input_dim=num_items, output_dim=latent_dim, name='item_embedding', input_length=1)
    user_latent = Flatten()(MF_Embedding_User(user_input))
    item_latent = Flatten()(MF_Embedding_Item(item_input))
    predict_vector = Multiply()([user_latent, item_latent])
    prediction = Dense(1, activation='sigmoid', name='prediction')(predict_vector)

    model = Model(inputs=[user_input, item_input], outputs=prediction)

    return model


def load_dict_map(file_name, is_inverse=False):
    """

    :param file_name:
    :param is_inverse: 判断key是真实id，还是训练id
    :return: 训练id与真实id的字典，key为训练id，value为真实id(is_inverse参数为False时)
    """
    dict_map = {}
    with open(file_name, encoding='UTF-8') as f:
        line = f.readline()
        while line != None and line != '':
            info_list = line.split('\t')
            if is_inverse:
                dict_map[info_list[1].strip('\n')] = info_list[0]
            else:
                dict_map[info_list[0]] = info_list[1].strip('\n')
            line = f.readline()
    return dict_map


def load_negative_file(filename):
    """
    加载负样本文件
    :param self:
    :param filename:
    :return: 返回一个列表list，每一个位置为i的元素也是个列表，包含了stu_id为i的学生未曾有过交互的book
    """
    negativeList = []
    with open(filename, "r") as f:
        line = f.readline()
        while line != None and line != "":
            arr = line.split("\t")
            negatives = []
            for x in arr[1:]:
                negatives.append(int(x))
            negativeList.append(negatives)
            line = f.readline()
    return negativeList


stu_dict = load_dict_map('./web/recommend_data/B5_stuDic.txt')
print([(k, v) for k, v in stu_dict.items()][0:5])
stu_inverse_dict = load_dict_map('./web/recommend_data/B5_stuDic.txt', is_inverse=True)
print([(k, v) for k, v in stu_inverse_dict.items()][0:5])
book_dict = load_dict_map('./web/recommend_data/B5_bookDic.txt')
negativeList = load_negative_file('./web/recommend_data/B5.negative')


#key为书名，value为借阅的数量
book_dict2 = {}

with open('./web/recommend_data/B5.txt', encoding='UTF-8') as f:
    for line in f:
        if line == '':
            continue
        book_name = line.split(';')[3]
        if not (book_name in book_dict2):
            book_dict2[book_name] = 1
        else:
            book_dict2[book_name] += 1


# key为学院，value也是dict(和上面一样，这个dict的key是书名，value是借阅数量)
school_book_dict = {}

with open('./web/recommend_data/B5_new.txt', encoding='UTF-8') as f:
    for line in f:
        if line == '':
            continue
        info_list = line.split(';')
        book_name = info_list[3]
        school_name = info_list[-1].strip()
        if school_name not in school_book_dict:
            name_value_dict = {book_name: 1}
            school_book_dict[school_name] = name_value_dict
        else:
            tmp_dict = school_book_dict[school_name]
            if not (book_name in tmp_dict):
                tmp_dict[book_name] = 1
            else:
                tmp_dict[book_name] += 1


def get_hot_book(topK, school="all"):
    """
    获取借阅量前topK的书籍列表
    :param topK:
    :return:
    """
    global book_dict2, school_book_dict
    klarget_name_list = heapq.nlargest(topK, book_dict2.keys(), key=book_dict2.get)
    klarget_count_list = [book_dict2[name] for name in klarget_name_list]
    if school != "全校学生":
        specific_dict = school_book_dict[school]
        klarget_name_list = heapq.nlargest(topK, specific_dict.keys(), key=specific_dict.get)
        klarget_count_list = [specific_dict[name] for name in klarget_name_list]
    print(klarget_name_list)
    print(klarget_count_list)
    return klarget_name_list, klarget_count_list


# topk_loc_list, topk_count_list = get_hot_book(20)


def get_recommend_list(idr):
    """
    针对一个用户id，返回推荐列表
    :param idx:
    :return:
    """
    global negativeList, model
    items = negativeList[idr]
    print(idr)
    print("22222222222222222222", len(items))
    # Get prediction scores
    map_item_score = {}
    users = np.full(len(items), idr, dtype='int32').reshape(-1, 1)
    print(users.shape)
    # 得到所有这99个item的预估分
    print(model.summary())
    print("=================朱大竞==============", model.predict([np.array([1]), np.array([1])], batch_size=1))
    predictions = model.predict([users, np.array(items).reshape(-1, 1)], batch_size=199)
    for i in range(len(items)):
        item = items[i]
        map_item_score[item] = predictions[i]

    # Evaluate top rank list
    ranklist = heapq.nlargest(5, map_item_score, key=map_item_score.get)
    return ranklist


def add_random_school(file_path=r".\recommend_data\B5.txt"):
    """
    按照李师姐的要求，为每个学生随机生成一个学院，虽然我觉得不大好鸭
    :param file_path:
    :return:
    """
    new_B5_file = open(r".\recommend_data\B5_new.txt", "w", encoding='utf-8')
    school_list = ['化学化工学院', '数学科学学院', '环境科学与工程学院', '农业与生物学院', '安泰经济与管理学院', '医学院', '生命科学技术学院', '生物医学工程学院',
                   '船舶海洋与建筑工程学院', '电子信息与电气工程学院', '机械与动力工程学院', '药学院', '材料科学与工程学院', '媒体与设计学院', '航空航天学院(空天科学技术研究院)',
                   '巴黎高科卓越工程师学院', '物理与天文学院', '外国语学院', '密西根学院', '国际与公共事务学院']
    stuNo_dict = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line[:-1]
            if line == '':
                continue
            tmp_stuNo = line.split(";")[1]
            if tmp_stuNo not in stuNo_dict:
                stuNo_dict[tmp_stuNo] = school_list[random.randint(0, len(school_list) - 1)]
            line += (";" + stuNo_dict[tmp_stuNo] + "\n")
            new_B5_file.write(line)
    print(len(stuNo_dict))


if __name__ == '__main__':
    # 测试代码
    pass

    # add_random_school()

    # stu_dict = load_dict_map('./recommend_data/B5_stuDic.txt')
    # print(stu_dict['4432'])
    # model = get_recommend_model(11767, 20089)
    # model.load_weights('./trained_model/test2.h5')
    # print(model.predict([np.array([1]), np.array([1])], batch_size=1))

# 注意: 在模块不当主模块运行的时候，当前工作路径与当主模块运行时的工作路径不一定一样
# print(os.getcwd())
# add_random_school()

model = get_recommend_model(11767, 20089)
model.load_weights('./web/trained_model/test2.h5')
# 测试代码
print("=================朱大竞==============", model.predict([np.array([1]), np.array([1])], batch_size=1))
