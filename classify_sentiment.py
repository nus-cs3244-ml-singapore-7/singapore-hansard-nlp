import argparse
import json
import os

import torch
from transformers import XLMRobertaForSequenceClassification, XLMRobertaTokenizerFast

DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def create_arg_parser():
    parser = argparse.ArgumentParser(
        description='Perform sentiment classification on Singapore Hansard using XLM-RoBERTa model')

    parser.add_argument('input_dir_path', type=str,
        help='Path of directroy to read JSON files from.')

    parser.add_argument('output_dir_path', type=str,
        help='Path of directroy to write JSON files to.')

    parser.add_argument('model_name_or_dir', type=str,
        help='Name or directory of model.')

    return parser

def main(
        input_dir_path,
        output_dir_path,
        model_name_or_dir):
    tokenizer = XLMRobertaTokenizerFast.from_pretrained(model_name_or_dir)
    model = XLMRobertaForSequenceClassification.from_pretrained(model_name_or_dir).to(DEVICE)
    model.eval()

    os.makedirs(output_dir_path, exist_ok=True)

    for file_name in os.listdir(input_dir_path):
        if file_name.endswith('.json'):
            count = 0
            input_file_path = os.path.join(input_dir_path, file_name)
            with open(input_file_path) as json_file:
                data = json.load(json_file)

                for session in data['sessions']:
                    for speech in session['speeches']:
                        content = []
                        for text in speech['content']:
                            inputs = tokenizer.encode(
                                text, padding=False, truncation=True, return_tensors='pt').to(DEVICE)

                            with torch.no_grad():
                                outputs = model(inputs).logits
                                predictions = torch.softmax(outputs, dim=-1)[0, 1].item()

                            content.append({ 'text': text, 'sentiment': round(predictions, 6) })
                            count += 1
                        speech['content'] = content

            output_file_path = os.path.join(output_dir_path, file_name)
            with open(output_file_path, 'w') as json_file:
                json.dump(data, json_file)

            print("File: {}, Count: {}".format(file_name, count))

if __name__ == '__main__':
    parser = create_arg_parser()
    args = parser.parse_args()
    main(
        args.input_dir_path,
        args.output_dir_path,
        args.model_name_or_dir)
