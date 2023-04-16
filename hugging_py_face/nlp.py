import json
import requests
from pandas import DataFrame
from typing import Text, List, Dict, Optional, Union

from .config_parser import ConfigParser


class NLP:
    def __init__(self, api_token):
        self.api_token = api_token

        config_parser = ConfigParser()
        self.config = config_parser.get_config_dict()

    def _query(self, inputs: Union[Text, List, Dict], parameters: Optional[Dict] = None, options: Optional[Dict] = None, model: Optional[Text] = None, task: Optional[Text] = None) -> Union[Dict, List]:
        api_url = f"{self.config['BASE_URL']}/{model if model is not None else self.config['TASK_MODEL_MAP'][task]}"

        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }

        data = {
            "inputs": inputs
        }

        if parameters is not None:
            data['parameters'] = parameters

        if options is not None:
            data['options'] = options

        response = requests.request("POST", api_url, headers=headers, data=json.dumps(data))
        return json.loads(response.content.decode("utf-8"))

    def _query_in_df(self, df: DataFrame, column: Text, parameters: Optional[Dict] = None, options: Optional[Dict] = None, model: Optional[Text] = None, task: Optional[Text] = None) -> Union[Dict, List]:
        return self._query(df[column].tolist(), parameters, options, model, task)

    def fill_mask(self, text: Union[Text, List], options: Optional[Dict] = None, model: Optional[Text] = None) -> List:
        """
        Fill in a masked portion(token) of a string or a list of strings.

        :param text: a string or list of strings to be filled. Each input must contain the [MASK] token.
        :param options: a dict of options. For more information, see the `detailed parameters for the fill mask task <https://huggingface.co/docs/api-inference/detailed_parameters#fill-mask-task>`_.
        :param model: the model to use for the fill mask task. If not provided, the recommended model from Hugging Face will be used.
        :return: a list of dicts or a list of lists (of dicts) containing the possible completions and their associated probabilities.
        """
        return self._query(text, options=options, model=model, task='fill-mask')

    def fill_mask_in_df(self, df: DataFrame, column: Text, options: Optional[Dict] = None, model: Optional[Text] = None) -> DataFrame:
        """
        Fill in the masked portion(token) of a column of strings in a DataFrame.

        :param df: a pandas DataFrame containing the strings to be filled.
        :param column: the column containing the strings to be filled.
        :param options: a dict of options. For more information, see the `detailed parameters for the fill mask task <https://huggingface.co/docs/api-inference/detailed_parameters#fill-mask-task>`_.
        :param model: the model to use for the fill mask task. If not provided, the recommended model from Hugging Face will be used.
        :return: a pandas DataFrame with the completions for the masked strings. Each completion added will be the one with the highest probability for that particular masked string. The completions will be added as a new column called 'predictions' to the original DataFrame.
        """
        predictions = self._query_in_df(df, column, options=options, model=model, task='fill-mask')

        if any(isinstance(prediction, list) for prediction in predictions):
            df['predictions'] = [prediction[0]['sequence'] for prediction in predictions]
        else:
            df['predictions'] = [predictions[0]['sequence']]

        return df

    def summarization(self, text: Union[Text, List], parameters: Optional[Dict] = None, options: Optional[Dict] = None, model: Optional[Text] = None) -> Union[Dict, List]:
        """
        Summarize a string or a list of strings.

        :param text: a string or list of strings to be summarized.
        :param parameters: a dict of parameters. For more information, see the `detailed parameters for the summarization task <https://huggingface.co/docs/api-inference/detailed_parameters#summarization-task>`_.
        :param options: a dict of options. For more information, see the `detailed parameters for the summarization task <https://huggingface.co/docs/api-inference/detailed_parameters#summarization-task>`_.
        :param model: the model to use for the summarization task. If not provided, the recommended model from Hugging Face will be used.
        :return: a dict or a list of dicts of the summarized string(s).
        """
        return self._query(text, parameters=parameters, options=options, model=model, task='summarization')

    def summarization_in_df(self, df: DataFrame, column: Text, parameters: Optional[Dict] = None, options: Optional[Dict] = None, model: Optional[Text] = None) -> DataFrame:
        """
        Summarize a column of strings in a DataFrame.

        :param df: a pandas DataFrame containing the strings to be summarized.
        :param column: the column containing the strings to be summarized.
        :param parameters: a dict of parameters. For more information, see the `detailed parameters for the summarization task <https://huggingface.co/docs/api-inference/detailed_parameters#summarization-task>`_.
        :param options: a dict of options. For more information, see the `detailed parameters for the summarization task <https://huggingface.co/docs/api-inference/detailed_parameters#summarization-task>`_.
        :param model: the model to use for the summarization task. If not provided, the recommended model from Hugging Face will be used.
        :return: a pandas DataFrame with the summarizations for the strings. The summarizations will be added as a new column called 'predictions' to the original DataFrame.
        """
        predictions = self._query_in_df(df, column, options=options, model=model, task='summarization')
        df['predictions'] = [prediction['summary_text'] for prediction in predictions]
        return df

    def question_answering(self, question: Text, context: Text, model: Optional[Text] = None) -> Dict:
        """
        Answer a question using the provided context.

        :param question: a string of the question to be answered.
        :param context: a string of context.
        :param model: the model to use for the question answering task. If not provided, the recommended model from Hugging Face will be used.
        :return: a dict of the answer.

        # TODO: check if questions can be answered without context
        """
        return self._query(
            {
                "question": question,
                "context": context
            },
            model=model,
            task='question-answering'
        )

    def sentence_similarity(self, source_sentence: Text, sentences: List, options: Optional[Dict] = None, model: Optional[Text] = None) -> List:
        """
        Calculate the semantic similarity between one text and a list of other sentences by comparing their embeddings.

        :param source_sentence: the string that you wish to compare the other strings with.
        :param sentences: a list of strings which will be compared against the source_sentence.
        :param options: a dict of options. For more information, see the `detailed parameters for the sentence similarity task <https://huggingface.co/docs/api-inference/detailed_parameters#sentence-similarity-task>`_.
        :param model: the model to use for the sentence similarity task. If not provided, the recommended model from Hugging Face will be used.
        :return: a list of similarity scores.
        """
        return self._query(
            {
                "source_sentence": source_sentence,
                "sentences": sentences
            },
            options=options,
            model=model,
            task='sentence-similarity'
        )

    def text_classification(self, text: Union[Text, List], options: Optional[Dict] = None, model: Optional[Text] = None) -> Union[Dict, List]:
        """
        Analyze the sentiment of a string or a list of strings.

        :param text: a string or list of strings to be analyzed.
        :param options: a dict of options. For more information, see the `detailed parameters for the summarization task <https://huggingface.co/docs/api-inference/detailed_parameters#text-classification-task>`_.
        :param model: the model to use for the text classification task. If not provided, the recommended model from Hugging Face will be used.
        :return: a dict or a list of dicts indicating the possible sentiments of the string(s) and their associated probabilities.
        """
        return self._query(text, options=options, model=model, task='text-classification')

    def text_classification_in_df(self, df: DataFrame, column: Text, options: Optional[Dict] = None, model: Optional[Text] = None) -> DataFrame:
        """
        Analyze the sentiment of a column of strings in a DataFrame.

        :param df: a pandas DataFrame containing the strings to be analyzed.
        :param column: the column containing the strings to be analyzed.
        :param options: a dict of options. For more information, see the `detailed parameters for the summarization task <https://huggingface.co/docs/api-inference/detailed_parameters#text-classification-task>`_.
        :param model: the model to use for the text classification task. If not provided, the recommended model from Hugging Face will be used.
        :return: a pandas DataFrame with the sentiment of the strings. Each sentiment added will be the one with the highest probability for that particular string. The sentiment will be added as a new column called 'predictions' to the original DataFrame.
        """
        predictions = self._query_in_df(df, column, options=options, model=model, task='text-classification')
        df['predictions'] = [prediction[0]['label'] for prediction in predictions]
        return df

    def text_generation(self, text: Union[Text, List], parameters: Optional[Dict] = None, options: Optional[Dict] = None, model: Optional[Text] = None) -> Union[Dict, List]:
        """
        Continue text from a prompt.

        :param text: a string to be generated from.
        :param parameters: a dict of parameters. For more information, see the `detailed parameters for the text generation task <https://huggingface.co/docs/api-inference/detailed_parameters#text-generation-task>`_.
        :param options: a dict of options. For more information, see the `detailed parameters for the text generation task <https://huggingface.co/docs/api-inference/detailed_parameters#text-generation-task>`_.
        :param model: the model to use for the text generation task. If not provided, the recommended model from Hugging Face will be used.
        :return: a dict or a list of dicts containing the generated text.
        """
        return self._query(text, parameters=parameters, options=options, model=model, task='text-generation')

    def zero_shot_classification(self, text: Union[Text, List], candidate_labels: List, parameters: Optional[Dict] = {}, options: Optional[Dict] = None, model: Optional[Text] = None) -> Union[Dict, List]:
        """
        Classify a sentence/paragraph to one of the candidate labels provided.

        :param text: a string or list of strings to be classified.
        :param candidate_labels: a list of strings that are potential classes for inputs.
        :param parameters: a dict of parameters excluding candidate_labels which is passed in as a separate argument. For more information, see the `detailed parameters for the zero shot classification task <https://huggingface.co/docs/api-inference/detailed_parameters#zeroshot-classification-task>`_.
        :param options: a dict of options. For more information, see the `detailed parameters for the zero shot classification task <https://huggingface.co/docs/api-inference/detailed_parameters#zeroshot-classification-task>`_.
        :param model: the model to use for the zero shot classification task. If not provided, the recommended model from Hugging Face will be used.
        :return: a dict or a list of dicts containing the labels and the corresponding the probability of each label.
        """
        parameters['candidate_labels'] = candidate_labels

        return self._query(
            text,
            parameters=parameters,
            options=options,
            model=model,
            task='zero-shot-classification'
        )

    def conversational(self, text: Union[Text, List], past_user_inputs: Optional[Text] = None, generated_responses: Optional[Text] = None, parameters: Optional[Dict] = None, options: Optional[Dict] = None, model: Optional[Text] = None) -> Union[Dict, List]:
        """
        Corresponds to any chatbot like structure: pass in some text along with the past_user_inputs and generated_responses to receive a response.

        :param text: a string or list of strings representing the last input(s) from the user in the conversation.
        :param past_user_inputs: a list of strings corresponding to the earlier replies from the user. Should be of the same length of generated_responses. Each response from the bot will contain past_user_inputs previously passed into the model.
        :param generated_responses: a list of strings corresponding to the earlier replies from the model. Each response from the bot will contain generated_responses from earlier replies from the model.
        :param parameters: a dict of parameters. For more information, see the `detailed parameters for the conversational task <https://huggingface.co/docs/api-inference/detailed_parameters#conversational-task>`_.
        :param options: a dict of options. For more information, see the `detailed parameters for the conversational task <https://huggingface.co/docs/api-inference/detailed_parameters#conversational-task>`_.
        :param model: the model to use for the conversational task. If not provided, the recommended model from Hugging Face will be used.
        :return: a dict or a list of dicts containing the response(s) from the bot.
        """
        inputs = {
            'text': text
        }

        if past_user_inputs is not None:
            inputs['past_user_inputs'] = past_user_inputs

        if generated_responses is not None:
            inputs['generated_responses'] = generated_responses

        return self._query(
            inputs,
            parameters=parameters,
            options=options,
            model=model,
            task='conversational'
        )

    def feature_extraction(self, text: Union[Text, List], options: Optional[Dict] = None, model: Optional[Text] = None) -> Union[Dict, List]:
        """
        Reads some text and outputs raw float values, that are usually consumed as part of a semantic database/semantic search.

        :param text: a string or a list of strings to get the features from.
        :param options: a dict of options. For more information, see the `detailed parameters for the feature extraction task <https://huggingface.co/docs/api-inference/detailed_parameters#feature-extraction-task>`_.
        :param model: the model to use for the feature extraction task. If not provided, the recommended model from Hugging Face will be used.
        :return: a list of dicts or a list of lists (of dicts) containing the representation of the features of the input(s).
        """
        return self._query(text, options=options, model=model, task='feature-extraction')