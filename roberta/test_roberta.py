from transformers import AutoTokenizer, AutoModel, AdamW, get_linear_schedule_with_warmup
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import argparse
import torch
import torch.nn as nn
import numpy as np
import json
from tqdm import tqdm
import random
import time
import os
from sklearn.metrics import f1_score, roc_auc_score

seed = 42
# fix random seed
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.backends.cudnn.enabled = False

# define model

class BERTModelForClassification(nn.Module):

    def __init__(self, model_name):
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        self.linear = nn.Linear(self.bert.config.hidden_size, 1)
    def forward(self, input_ids, attention_mask):
        hidden_states = self.bert(input_ids=input_ids,
                    attention_mask=attention_mask)[0] # batch, seq_len, emb_dim

        # get [CLS] embeddings
        cls_embeddings = hidden_states[:,0,:]
        logits = self.linear(cls_embeddings)

        outputs = torch.sigmoid(logits)
        return outputs        


# define loader

class PropaFakeDataset(Dataset):
    
    # 原代码
    def __init__(self, jsonl_path):
        self.tokenizer = AutoTokenizer.from_pretrained(args.model_name)
        
        self.data = []
        
        for line in open(jsonl_path,'r'):
            inst = json.loads(line)
            label = inst['label']
            inputs = self.tokenizer(inst['txt'], max_length=args.max_sequence_length, padding="max_length", truncation=True)
            self.data.append({
                'input_ids':inputs['input_ids'],
                'attention_mask': inputs['attention_mask'],
                'label': label
            })
        
            
        
    def __len__(self):
        # 200K datapoints
        return len(self.data)

    def __getitem__(self, idx):
        
        return self.data[idx]['input_ids'], self.data[idx]['attention_mask'], self.data[idx]['label']
    
    def collate_fn(self, batch):
        # print(batch)
        input_ids = torch.cuda.LongTensor([inst[0] for inst in batch])
        attention_masks = torch.cuda.LongTensor([inst[1]for inst in batch])
        labels = torch.cuda.FloatTensor([inst[2]for inst in batch])

        return input_ids, attention_masks, labels

# configuration
parser = argparse.ArgumentParser()
parser.add_argument('--max_sequence_length', default=512)
parser.add_argument('--model_name', default='roberta-large')


# zhuzhi 
# parser.add_argument('--data_dir', default='../data/')
parser.add_argument('--data_dir', default='/data/zz/FakingFakeNews/data')
parser.add_argument('--warmup_epoch', default=5, type=int)
parser.add_argument('--max_epoch', default=30, type=int)
parser.add_argument('--batch_size', default=2, type=int)
parser.add_argument('--eval_batch_size', default=2, type=int)
parser.add_argument('--accumulate_step', default=8, type=int)

# zhuzhi 指定模型位置
parser.add_argument('--checkpoint_path', type=str,default='/data/zz/FakingFakeNews/roberta/outputs/roberta/gossipcop/gossipcop_0.2/best.pt')

timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
args = parser.parse_args()

output_dir = '/'.join(args.checkpoint_path.split('/')[:-1])
# init model and tokenizer
# tokenizer = AutoTokenizer.from_pretrained(args.model_name)


#zhuzhi 2024/6/21
# 指定GPU
torch.cuda.set_device(3)


print('开始读取模型。。。')


# zhuzhi 这里手动下载好了模型/data/zz/FakingFakeNews/model/roberta-large
# model = BERTModelForClassification(args.model_name).cuda()
model = BERTModelForClassification("/data/zz/FakingFakeNews/model/roberta-large").cuda()




# define loss
critera = nn.BCELoss()
model_path = args.checkpoint_path

print('开始读取训练好的模型参数。。。')

checkpoint = torch.load(model_path)
model.load_state_dict(checkpoint['model'], strict=True)    
test_output_file = os.path.join(output_dir, 'test_pred.json')


print('开始读取数据。。。')

# init loader

# zhuzhi 修改测试集位置
# test_set = PropaFakeDataset(os.path.join(args.data_dir,'politifact_test.jsonl'))
test_set = PropaFakeDataset(os.path.join(args.data_dir,'politifact_test.jsonl'))
test_loader = DataLoader(test_set, batch_size=args.eval_batch_size, shuffle=False, collate_fn=test_set.collate_fn)


print('开始测试。。。')

with torch.no_grad():
    model.eval()
    test_outputs = []
    test_labels = []
    
    for _, (input_ids, attn_mask, labels) in enumerate(test_loader):
        outputs = model(input_ids, attention_mask=attn_mask).view(-1)
        test_outputs.append(outputs) 
        test_labels.append(labels)

    test_outputs = torch.cat(test_outputs, dim=0) # n_sample,
    test_labels = torch.cat(test_labels, dim=0) # n_sample,

    test_outputs_bool = test_outputs > 0.5
    test_labels_bool = test_labels == 1 # convert to float tensor

    test_accuracy = torch.sum(test_outputs_bool == test_labels_bool) / len(test_labels)


    # zhuzhi 2024/6/24 还要分别计算label=True的准确率与label=False的准确率
    test_true_accuracy = torch.sum(test_labels_bool[test_labels_bool == 1] == test_outputs_bool[test_labels_bool == 1]) / torch.sum(test_labels_bool == 1)
    test_false_accuracy = torch.sum(test_labels_bool[test_labels_bool == 0] == test_outputs_bool[test_labels_bool == 0]) / torch.sum(test_labels_bool == 0)
    print(f"测试集结果： 真新闻准确率：{test_true_accuracy * 100:.2f}，假新闻准确率：{test_false_accuracy * 100:.2f}， 分类准确率: {test_accuracy * 100:.2f}.")

    test_auc = roc_auc_score(test_labels.cpu().numpy(), test_outputs.detach().cpu().numpy())
    print(f"Test AUC: {test_auc}. ")
    
    test_f1 = f1_score(test_labels.cpu().numpy(), np.array([1 if l > 0.5 else 0 for l in test_outputs]))
    print(f"Test F1: {test_f1}. ")
    test_outputs = [float(o) for o in test_outputs]
    with open(test_output_file,'w') as f:
        json.dump({'output':test_outputs}, f)