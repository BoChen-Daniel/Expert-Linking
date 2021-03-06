import json
import numpy as np
import random
from paper_config import configs
# from mongo_online import mongo
# from bson import ObjectId
import torch
from transformers import BertTokenizer
from collections import defaultdict
from operator import itemgetter

class process_matching_data:
    def __init__(self, bertTokenizer):
        self.bertTokenizer = bertTokenizer
        self._load_raw_data()     

    def _load_raw_data(self):
        # with open("../data/news_data/0_430_entity_seq.json", 'r') as files:
        #     self.raw_data = json.load(files)
        # # print("total_raw_data: ", len(self.raw_data))ss

        # with open("../data/news_data/430News.json", 'r') as files:
        #     self.entity_data = json.load(files)

        paper_data_dir = "/home/chenbo/entity_linking/data/"
        # train_data
        with open(paper_data_dir + "paper_data/train_author_index.json", 'r') as files:
            self.train_author_data = json.load(files) 
        # with open(paper_data_dir + "paper_data/test_author_filter_cna_5_profile.json", 'r') as files:
        #     self.train_author_data = json.load(files) 
        
        # test_data
        with open(paper_data_dir + "paper_data/test_author_cna_filter_5_index.json", 'r') as files:
            self.test_author_data = json.load(files)

        with open(paper_data_dir + "paper_data/na_v1_pub_uuid.json", 'r') as files:
            self.paper_info = json.load(files)

        # self.paper_ids = list(self.paper_data.keys())
        # print(len(self.train_author_data))
        # print(configs["train_max_papers_each_author"])
        # print(configs["train_neg_sample"])
        # exit()
        self.train_author2name, self.filter_train_author = self.filter_raw_author_data(self.train_author_data, configs["train_max_papers_each_author"] * 2, configs["train_neg_sample"])
        self.test_author2name, self.filter_test_author = self.filter_raw_author_data(self.test_author_data, configs["train_max_papers_each_author"] + 1, configs["test_author_neg_sample"])
        
        print("Paper: Train_author: {} Test_author: {}".format(len(self.train_author2name), len(self.test_author2name)))
        # exit()
    def filter_raw_author_data(self, author_dict, min_paper, neg_sample):
        author_data = {}
        namepaper2pid = {}
        author2name = {}
        for author_name in author_dict:
            author_papers = author_dict[author_name]
            if(len(author_papers) < (neg_sample + 1)):
                continue
            tmp_author_data = {}
            tmp_author2name = {}
            for author_id, papers in author_papers.items():
                if(len(set(papers)) < min_paper):
                    continue
                tmp_author_data[author_id] = papers
                tmp_author2name[author_id] = author_name
            if(len(tmp_author_data) > neg_sample):
                author_data[author_name] = tmp_author_data
                author2name = {**author2name, **tmp_author2name}
        return author2name, author_data



    def generate_train_data(self, ins_num):
        sampling_pattern = [2]
        instance = []
        # flag = False
        # print(mode)
        author2name = self.train_author2name
        author_dict = self.filter_train_author
        # namepaper2pid = self.train_namepaper2pid
        # author_dict = self.filter_train_author
        # print("begin_train: ", len(author2name))
        author_list = list(author2name.keys())
        # random.seed(configs["seed"])
        # random.shuffle(author_list)
        count = 0
        # sample_author_id = random.sample(author_list, ins_num)

        sample_author_id = np.random.choice(author_list, size = ins_num, replace=True)
        multi_sampling = np.random.choice(sampling_pattern, size = ins_num, replace=True)
        count_0 = 0
        count_1 = 0
        count_2 = 0
        for pat in multi_sampling:
            if(pat == 0):
                count_0 += 1
            elif(pat == 1):
                count_1 += 1
            elif(pat == 2):
                count_2 += 1
            else:
                print("sampling error!")
                exit()
        print("Sampling Pattern 1-1: {} 1-many: {} many-many: {}".format(count_0, count_1, count_2)) 
        # ttt = [sample_author_id[0], sample_author_id[0]]
        for (author_id, ins_pat) in zip(sample_author_id, multi_sampling):
            author_name = author2name[author_id]
            whole_author_list = list(author_dict[author_name].keys())
            # print(len(whole_author_list))
            whole_author_list.remove(author_id)
            # print(len(whole_author_list))
            # random.seed(configs["seed"])
            neg_author_lists = random.sample(whole_author_list, configs["train_neg_sample"])
            # for neg_author_id in whole_author_list:
            each_ins = (ins_pat, author_name, author_id, neg_author_lists)
            # print(each_ins)
            
            tag, tokenizer_ins = self.tokenizer_padding(each_ins, author_dict)
            if(tag == False):
                continue
            count += 1
            instance.append(tokenizer_ins)
        # exit()
        return instance

    def generate_test_data(self, ins_num):
        instance = []

        author2name = self.test_author2name
        author_dict = self.filter_test_author
        # print("begin_test: ", len(author2name))
        # namepaper2pid = self.train_namepaper2pid
        # author_dict = self.filter_train_author
        author_list = list(author2name.keys())
        # random.seed(configs["seed"])
        sample_author_id = np.random.choice(author_list, size = ins_num, replace=True)
        for author_id in sample_author_id:
            author_name = author2name[author_id]
            whole_author_list = list(author_dict[author_name].keys())
            # print(len(whole_author_list))
            whole_author_list.remove(author_id)
            # print(len(whole_author_list))
            random.seed(1)
            neg_author_lists = random.sample(whole_author_list, configs["test_author_neg_sample"])
            # for neg_author_id in neg_author_lists:
            each_ins = (author_name, author_id, neg_author_lists)
            tag, tokenizer_ins = self.test_tokenizer_padding(each_ins, author_dict)
            if(tag == False):
                continue
            instance.append(tokenizer_ins)
        return instance

    def test_tokenizer_padding(self, each, author_dict):
        author_name, author_id, neg_author_id_list = each


        author_a, author_b, author_c_list = self.get_test_author_encoder(author_id, neg_author_id_list,  author_name, author_dict)
        
        # neg_author

        
        return True, (author_a, author_b, author_c_list)


    def get_test_author_encoder(self, author_id, neg_author_id_list, author_name, author_dict):
        input_ids_list_a = []
        attention_masks_list_a = []

        input_ids_list_b = []
        attention_masks_list_b = []

        per_input_ids_list_c = []
        per_attention_masks_list_c = []

        author_papers = author_dict[author_name][author_id]
        # neg_author_papers = author_dict[author_name][neg_author_id]
        # print(author_papers)
        # print(paper_id)
        
            # print(author_name, author_id, author_papers)
        # random.shuffle(author_papers)
        author_papers_set = set(author_papers)
        author_papers_list = list(author_papers_set)
        # random.seed(configs["seed"])
        sample_papers_a = random.sample(author_papers_list, 1)
        
        remain_papers_list = list(author_papers_set - set(sample_papers_a))
        # random.seed(configs["seed"])s
        # sample_papers_b = random.sample(remain_papers_list, configs["train_max_papers_each_author"])
        sample_papers_b = random.sample(remain_papers_list, min(500, len(remain_papers_list)))

        for paper_id in sample_papers_a:
            tag, input_ids, attention_masks = self.paper_encoder(paper_id)
            if(tag == False):
                continue
                # exit()
            input_ids_list_a.append(input_ids)
            attention_masks_list_a.append(attention_masks)

        for paper_id in sample_papers_b:
            tag, input_ids, attention_masks = self.paper_encoder(paper_id)
            if(tag == False):
                continue
                # exit()
            input_ids_list_b.append(input_ids)
            attention_masks_list_b.append(attention_masks)

        for neg_author_id in neg_author_id_list:
            neg_author_papers = author_dict[author_name][neg_author_id]

            neg_author_set = set(neg_author_papers)
            neg_autor_list = list(neg_author_set)
            # random.seed(configs["seed"])
            # sample_papers_c = random.sample(neg_autor_list, configs["train_max_papers_each_author"])
            sample_papers_c = random.sample(neg_autor_list, min(500, len(neg_autor_list)))
            
            input_ids_list_c = []
            attention_masks_list_c = []           

            for paper_id in sample_papers_c:
                tag, input_ids, attention_masks = self.paper_encoder(paper_id)
                if(tag == False):
                    continue
                    # exit()
                input_ids_list_c.append(input_ids)
                attention_masks_list_c.append(attention_masks)
            per_input_ids_list_c.append(input_ids_list_c)
            per_attention_masks_list_c.append(attention_masks_list_c)

        return (input_ids_list_a, attention_masks_list_a), (input_ids_list_b, attention_masks_list_b), (per_input_ids_list_c, per_attention_masks_list_c)



    def tokenizer_padding(self, each, author_dict):
        ins_pat, author_name, author_id, neg_author_id_list = each

        author_a, author_b, author_c_list = self.get_author_encoder(ins_pat, author_id, neg_author_id_list, author_name, author_dict)

        
        return True, (author_a, author_b, author_c_list)


    def get_author_encoder(self, ins_pat, author_id, neg_author_id_list, author_name, author_dict, paper_id = None):
        attr_input_ids_list_a = []
        attr_attention_masks_list_a = []

        attr_input_ids_list_b = []
        attr_attention_masks_list_b = []


        attr_per_input_ids_list_c = []
        attr_per_attention_masks_list_c = []

        author_papers = author_dict[author_name][author_id]
        # neg_author_papers = author_dict[author_name][neg_author_id]
        # print(author_papers)
        # print(paper_id)
        
            # print(author_name, author_id, author_papers)
        # random.shuffle(author_papers)
        author_papers_set = set(author_papers)
        author_papers_list = list(author_papers_set)
        # print(author_papers_list)
        # random.seed(configs["seed"])
        if(ins_pat == 0):
            sample_papers_a = random.sample(author_papers_list, 1)
            
            remain_papers_list = list(author_papers_set - set(sample_papers_a))
            # random.seed(configs["seed"])
            sample_papers_b = random.sample(remain_papers_list, 1)

            # print(sample_papers_a)
            # print(sample_papers_b)
            for paper_id in sample_papers_a:
                tag, attr_input_ids, attr_attention_masks = self.paper_encoder(paper_id)
                if(tag == False):
                    continue
                attr_input_ids_list_a.append(attr_input_ids)
                attr_attention_masks_list_a.append(attr_attention_masks)

            for paper_id in sample_papers_b:
                tag, attr_input_ids, attr_attention_masks = self.paper_encoder(paper_id)
                if(tag == False):
                    continue

                attr_input_ids_list_b.append(attr_input_ids)
                attr_attention_masks_list_b.append(attr_attention_masks)

            for neg_author_id in neg_author_id_list:
                neg_author_papers = author_dict[author_name][neg_author_id]

                neg_author_set = set(neg_author_papers)
                neg_autor_list = list(neg_author_set)
                # random.seed(configs["seed"])
                sample_papers_c = random.sample(neg_autor_list, 1)
                        
                attr_input_ids_list_c = []
                attr_attention_masks_list_c = []   
                for paper_id in sample_papers_c:
                    tag, attr_input_ids, attr_attention_masks = self.paper_encoder(paper_id)
                    if(tag == False):
                        continue
                        # exit()
                    attr_input_ids_list_c.append(attr_input_ids)
                    attr_attention_masks_list_c.append(attr_attention_masks)
                attr_per_input_ids_list_c.append(attr_input_ids_list_c)
                attr_per_attention_masks_list_c.append(attr_attention_masks_list_c)

        elif(ins_pat == 1):
            sample_papers_a = random.sample(author_papers_list, 1)
            
            remain_papers_list = list(author_papers_set - set(sample_papers_a))
            # random.seed(configs["seed"])
            sample_papers_b = random.sample(remain_papers_list, configs["train_max_papers_each_author"])

            # print(sample_papers_a)
            # print(sample_papers_b)
            for paper_id in sample_papers_a:
                tag, attr_input_ids, attr_attention_masks = self.paper_encoder(paper_id)
                if(tag == False):
                    continue
                    # exit()
                attr_input_ids_list_a.append(attr_input_ids)
                attr_attention_masks_list_a.append(attr_attention_masks)

            for paper_id in sample_papers_b:
                tag, attr_input_ids, attr_attention_masks = self.paper_encoder(paper_id)
                if(tag == False):
                    continue
                attr_input_ids_list_b.append(attr_input_ids)
                attr_attention_masks_list_b.append(attr_attention_masks)

            for neg_author_id in neg_author_id_list:
                neg_author_papers = author_dict[author_name][neg_author_id]

                neg_author_set = set(neg_author_papers)
                neg_autor_list = list(neg_author_set)
                # random.seed(configs["seed"])
                sample_papers_c = random.sample(neg_autor_list, configs["train_max_papers_each_author"])
     
                attr_input_ids_list_c = []
                attr_attention_masks_list_c = []   
                for paper_id in sample_papers_c:
                    tag, attr_input_ids, attr_attention_masks = self.paper_encoder(paper_id)
                    if(tag == False):
                        continue
                        # exit()
                    attr_input_ids_list_c.append(attr_input_ids)
                    attr_attention_masks_list_c.append(attr_attention_masks)

                attr_per_input_ids_list_c.append(attr_input_ids_list_c)
                attr_per_attention_masks_list_c.append(attr_attention_masks_list_c)            
        
        elif(ins_pat == 2):
            sample_papers_a = random.sample(author_papers_list, configs["train_max_papers_each_author"])
            
            remain_papers_list = list(author_papers_set - set(sample_papers_a))
            # random.seed(configs["seed"])
            sample_papers_b = random.sample(remain_papers_list, configs["train_max_papers_each_author"])

            # print(sample_papers_a)
            # print(sample_papers_b)
            for paper_id in sample_papers_a:
                tag, attr_input_ids, attr_attention_masks = self.paper_encoder(paper_id)
                if(tag == False):
                    continue
                    # exit()
                attr_input_ids_list_a.append(attr_input_ids)
                attr_attention_masks_list_a.append(attr_attention_masks)

            for paper_id in sample_papers_b:
                tag, attr_input_ids, attr_attention_masks = self.paper_encoder(paper_id)
                if(tag == False):
                    continue

                attr_input_ids_list_b.append(attr_input_ids)
                attr_attention_masks_list_b.append(attr_attention_masks)

            for neg_author_id in neg_author_id_list:
                neg_author_papers = author_dict[author_name][neg_author_id]

                neg_author_set = set(neg_author_papers)
                neg_autor_list = list(neg_author_set)
                # random.seed(configs["seed"])
                sample_papers_c = random.sample(neg_autor_list, configs["train_max_papers_each_author"])
                     
                attr_input_ids_list_c = []
                attr_attention_masks_list_c = []   
                for paper_id in sample_papers_c:
                    tag, attr_input_ids, attr_attention_masks = self.paper_encoder(paper_id)
                    if(tag == False):
                        continue
                        # exit()
                    attr_input_ids_list_c.append(attr_input_ids)
                    attr_attention_masks_list_c.append(attr_attention_masks)
                attr_per_input_ids_list_c.append(attr_input_ids_list_c)
                attr_per_attention_masks_list_c.append(attr_attention_masks_list_c)   
        else:
            print("NO SUCH PATTERN!")
            exit()

        return (attr_input_ids_list_a, attr_attention_masks_list_a), \
            (attr_input_ids_list_b, attr_attention_masks_list_b), \
            (attr_per_input_ids_list_c, attr_per_attention_masks_list_c)

            
    # def get_res_abs(self, papers_attr):
    #     # print(papers_attr)
    #     try:
    #         title = papers_attr["title"].strip().lower()
    #     except:
    #         title = ""

    #     # try:
    #         # abstract = papers_attr["abstract"].strip().lower()
    #     # except:
    #         # abstract = ""    
    
    #     # whole_info = keywords_info
    #     # whole_info_str = title + ' ' + abstract
    #     whole_info_str = title
    #     # print(whole_info_str)
    #     if(len(whole_info_str.strip().lower()) == 0):
    #         return False, ""
    #     else:
    #         return True, whole_info_str

    def get_res_abs(self, papers_id):
        split_info = papers_id.split('-')
        pid = str(split_info[0])
        author_index = int(split_info[1])
        papers_attr = self.paper_info[pid]
        # print(papers_attr)
        name_info = set()
        org_info = set()
        keywords_info = set()
        try:
            title = papers_attr["title"].strip().lower()
        except:
            title = ""

        try:
            venue = papers_attr["venue"].strip().lower()
        except:
            venue = ""

        try:
            keywords = papers_attr["keywords"]
        except:
            keywords = []
        for ins in keywords:
            keywords_info.add(ins.strip().lower())

        paper_authors = papers_attr["authors"]
        for ins_author_index in range(len(paper_authors)):
            ins_author = paper_authors[ins_author_index]

            try:
                name = ins_author["name"].strip().lower()
            except:
                name = ""

            
            try:
                orgnizations =ins_author["org"].strip().lower()
            except:
                orgnizations = ""

            if(ins_author_index != author_index):
                if(name != ""):
                    name_info.add(name)
                
            if(orgnizations.strip().lower() != ""):
                org_info.add(orgnizations)

        name_str = " ".join(name_info).strip()
        org_str = " ".join(org_info).strip()
        keywords_str = " ".join(keywords_info).strip()


        # whole_info = keywords_info
        name_info_str = name_str.strip()
        whole_info_str = title + ' ' + keywords_str + " " + org_str + ' ' + venue
        whole_info_str = whole_info_str.strip()
        # print(whole_info_str)
        # if(len(whole_info_str) == 0) or (len(name_info_str) == 0):
        #     return False, "", ""
        # total_info_str = title + " " + keywords_str + " " + " " + org_str + " " + venue

        return True, whole_info_str


    # def get_res_abs(self, papers_id):
    #     split_info = papers_id.split('-')
    #     pid = str(split_info[0])
    #     author_index = int(split_info[1])
    #     papers_attr = self.paper_info[pid]
    #     # print(papers_attr)
    #     try:
    #         title = papers_attr["title"].strip().lower()
    #     except:
    #         title = ""

    #     try:
    #         abstract = papers_attr["abstract"].strip().lower()
    #     except:
    #         abstract = ""
    #     # print(abstract)
    #     # exit()
    #     whole_info_str = title + " " + abstract
    #     whole_info_str = whole_info_str.strip()

    #     return True, whole_info_str


    def paper_encoder(self, paper_id):
    
        # papers_attr = self.paper_info[paper_id]
        tag, attr_str = self.get_res_abs(paper_id)
        if(tag == False):
            return False, [], []
        # print("paper:", paper_str)
        attr_outputs = self.bertTokenizer.encode_plus(attr_str, max_length = configs["train_max_paper_length"])
        attr_input_ids = attr_outputs["input_ids"]
        # print(len(attr_input_ids))
        attr_attention_masks = [1] * len(attr_input_ids)
        # type_ids = [0] * 

        attr_padding_length = configs["train_max_paper_length"] - len(attr_input_ids)
        attr_padding_input_ids = attr_input_ids + [0] * attr_padding_length
        # qa_padding_token_type_ids = qa_token_type_ids + [1] * padding_length
        attr_padding_attention_masks = attr_attention_masks + [0] * attr_padding_length
        # qa_padding_positions_id = qa_position_ids + [0] * padding_length  


        return True, attr_padding_input_ids, attr_padding_attention_masks


if __name__ == "__main__":
    output_dir = "/home/chenbo/entity_linking/bert_generator/bert-base-multilingual-cased/"
    bertTokenizer = BertTokenizer.from_pretrained(output_dir)
    # model = process_data_via_bert(bertTokenizer)
    model = process_matching_data(bertTokenizer)
    ins = model.generate_data(1, "TRAIN")
    
    # print(len(ins))
    # print(np.array(ins[0]).shape)
    # inss = ins[0]
    # print(np.array(inss[0]).shape)
    # print(inss[0])
    # print(np.array(inss[2]).shape)
    # print(np.array(inss[2])[:, :10])

    # print(np.array(inss[1]).shape)
    # print(np.array(inss[2]).shape)
    # print(np.array(inss[3]).shape)
    # print(np.array(inss[4]).shape)
    # print(np.array(inss[5]).shape)
    # # print(np.array(inss[4][0]).shape)
    # # print(np.array(inss[4][1]).shape)
    # for i in inss[4]:
    #     print(len(i))
    # model.process_whole_instances()

