import emoji
import jieba
import matplotlib.pyplot as plt
import pandas as pd
from aip import AipNlp
from sklearn import metrics
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# Baidu_Aip密钥
APP_ID = '14963270'
API_KEY = 'DzcClKytSKKGpbTxdSFUcyif'
SECRET_KEY = 'IIIiZbKyHdFDqA7xq17kb8wS3elRVF7a'
# 加载百度Ai自然语言处理
client = AipNlp(APP_ID, API_KEY, SECRET_KEY)


# 评星数量>3作为正向情感，取值为1；反之视作负向情感，取值为0
def make_label(df):
    df["sentiment"] = df["star"].apply(lambda x: 1 if x > 3 else 0)


def chinese_word_cut(mytext):
    return " ".join(jieba.cut(mytext))


def get_custom_stopwords(stop_words_file):
    with open(stop_words_file, encoding='gbk') as f:
        stopwords = f.read()
    stopwords_list = stopwords.split('\n')
    custom_stopwords_list = [i for i in stopwords_list]
    return custom_stopwords_list


# 调用百度api情感分析
def get_sentiment(text):
    # print(emoji.demojize(text))
    try:
        sitems = client.sentimentClassify(emoji.demojize(text))['items'][0]
        # print(sitems['positive_prob'])
        return sitems['positive_prob']
    except Exception as e:
        print()


# 模型优度的可视化展现
def visualize(text, y_test, y_pred):
    fpr, tpr, _ = metrics.roc_curve(y_test, y_pred, pos_label=1)
    auc = metrics.auc(fpr, tpr)

    # 负号的正常显示
    plt.rcParams['axes.unicode_minus'] = False
    # 设置绘图风格
    plt.style.use('ggplot')

    # 绘制ROC曲线
    plt.plot(fpr, tpr, '')
    # 绘制参考线
    plt.plot((0, 1), (0, 1), 'r--')
    # 添加文本注释
    plt.text(0.5, 0.5, 'ROC=%.2f' % auc)
    # 设置坐标轴标签和标题
    plt.title(text + ' - AUC')
    plt.xlabel('1-specificity')
    plt.ylabel('Sensitivity')

    # 去除图形顶部边界和右边界的刻度
    plt.tick_params(top='off', right='off')
    # 图形显示
    plt.show()


# 数据读入
df = pd.read_excel('ranks.xlsx', sheetname=0)
make_label(df)
# 把特征和标签拆开
X = df[['comment']]
y = df.sentiment
# 每一行评论数据都进行分词
X['cutted_comment'] = X.comment.apply(chinese_word_cut)

# 拆分数据集合为训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)
# 处理中文停用词
stop_words_file = "chineseStopWords.txt"
stopwords = get_custom_stopwords(stop_words_file)

# 生成特征向量并降维
max_df = 0.8  # 在超过这一比例的文档中出现的关键词（过于平凡），去除掉。
min_df = 3  # 在低于这一数量的文档中出现的关键词（过于独特），去除掉。
vect = CountVectorizer(max_df=max_df,
                       min_df=min_df,
                       token_pattern=u'(?u)\\b[^\\d\\W]\\w+\\b',
                       stop_words=frozenset(stopwords))

term_matrix = pd.DataFrame(vect.fit_transform(X_train.cutted_comment).toarray(), columns=vect.get_feature_names())

# 朴素贝叶斯分类
nb = MultinomialNB()
pipe = make_pipeline(vect, nb)
print('Multinomial naive bayes_训练集交叉验证准确率：',
      cross_val_score(pipe, X_train.cutted_comment, y_train, cv=5, scoring='accuracy').mean())

# 拟合模型生成测试集
pipe.fit(X_train.cutted_comment, y_train)
y_pred = pipe.predict(X_test.cutted_comment)
accuracy1 = metrics.accuracy_score(y_test, y_pred)
print('Multinomial naive bayes_测试集预测准确率：', accuracy1)
print('Multinomial naive bayes混淆矩阵：')
print(metrics.confusion_matrix(y_test, y_pred))
# 模型优度的可视化展现
visualize('Multinomial naive bayes', y_test, y_pred)

# 对比百度ai的情感分析
print('waiting for baidu_ai analyse...')
y_pred_baidu = X_test.comment.apply(get_sentiment)
y_pred_baidu_normalized = y_pred_baidu.apply(lambda x: 1 if x > 0.5 else 0)
accuracy2 = metrics.accuracy_score(y_test, y_pred_baidu_normalized)
print('baidu_ai_测试集预测准确率：', accuracy2)
print('baidu_ai混淆矩阵：')
print(metrics.confusion_matrix(y_test, y_pred_baidu_normalized))
visualize('baidu_ai', y_test, y_pred_baidu_normalized)
