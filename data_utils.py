import os
import copy
import codecs
import tensorflow as tf


class DataUtils(object):
    def __init__(self):
        pass

    @staticmethod
    def tag_id(tag_char):
        tag_dict = dict()
        for i, v in enumerate(tag_char.split(",")):
            tag_dict[v] = i
        return tag_dict


class PrepareTagData(object):
    def __init__(self, conf, mode="train"):
        """
        mode: is what dataset can ben used. can be [train/test/validate]
        :param conf:
        :param mode:
        """
        self.dataPath = os.path.dirname(__file__)
        self.config = conf
        self.mode = mode
        self.vocabDict = self.__load_chinese_vocab()
        self.tagId = DataUtils.tag_id(conf.tag_char)
        self._sourceData = self.__read_dataset()

    def __load_chinese_vocab(self):
        cv = dict()
        with codecs.open(os.path.join(self.dataPath, "data/chinese_vocab.txt"), "r", "utf8") as f:
            for i, line in enumerate(f.readlines()):
                cv[line.strip()] = i
        return cv

    def __read_dataset(self):
        if self.mode == "train":
            dataset_path = os.path.join(self.dataPath, "data/trainset.txt")
        elif self.mode == "test":
            dataset_path = os.path.join(self.dataPath, "data/testset.txt")
        else:
            raise Exception("mode must be in [train/test]")

        if not os.path.exists(dataset_path):
            raise Exception("path [{}] not exists".format(dataset_path))

        with codecs.open(dataset_path, "r", "utf8") as fp:
            while True:
                a_line = fp.readline()
                if a_line:
                    yield a_line.rstrip("\n")
                else:
                    break

    def __is_end_sentence(self, cur):
        if cur.endswith(self.config.dataset_flag):
            return True
        return False

    def __next__(self):
        sentence_lst = []
        count = 0
        try:
            sentence = []
            while count < self.config.batch_size:
                cur = next(self._sourceData)
                if self.__is_end_sentence(cur):
                    if not sentence:
                        continue
                    count += 1
                    sentence_lst.append(copy.deepcopy(sentence))
                    sentence = []
                else:
                    sentence.append(cur)

        except StopIteration as iter_exception:
            if count == 0:
                raise iter_exception
        deal_x, deal_y = self.__deal_batch_data(sentence_lst)
        input_x, input_y = self.__padding_batch_data(deal_x, deal_y)
        return input_x, input_y

    def __iter__(self):
        return self

    @staticmethod
    def __padding_batch_data(deal_x, deal_y):
        max_len = max([len(x) for x in deal_x])
        deal_x = tf.keras.preprocessing.sequence.pad_sequences(
            deal_x, maxlen=max_len, padding="post", truncating="post", dtype="int32", value=0)
        deal_y = tf.keras.preprocessing.sequence.pad_sequences(
            deal_y, maxlen=max_len, padding="post", truncating="post", dtype="int32", value=0)
        return deal_x, deal_y

    def __deal_batch_data(self, sentence_lst):
        dataset_x = []
        dataset_y = []
        for sentence in sentence_lst:
            _x, _y = [], []
            for line in sentence:
                try:
                    line = line.split(" ")
                    if len(line) <= 1:
                        continue
                    vocab_id = self.vocabDict.get(line[0], -1)
                    if vocab_id == -1:
                        continue
                    tag_id = self.tagId.get(line[-1], -1)
                    if tag_id == -1:
                        continue
                except Exception as e:
                    continue
                _x.append(vocab_id)
                _y.append(tag_id)
            dataset_x.append(_x)
            dataset_y.append(_y)
        return dataset_x, dataset_y
