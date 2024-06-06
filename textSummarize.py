from flask import Flask, request, jsonify
import bs4 as bs
import urllib.request
import re
import nltk
import heapq
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

@app.route('/summarize', methods=['POST'])
def summarize():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        print(f"Fetching URL: {url}")
        scraped_data = urllib.request.urlopen(url)
        article = scraped_data.read()
    except Exception as e:
        error_message = f"Error fetching URL: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

    try:
        parsed_article = bs.BeautifulSoup(article, 'lxml')
        tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span']  # Add more tags as needed
        article_text = ""
        for tag in tags:
            elements = parsed_article.find_all(tag)
            for element in elements:
                article_text += element.text
        
        article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
        article_text = re.sub(r'\s+', ' ', article_text)
        formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text)
        formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)
        
        sentence_list = nltk.sent_tokenize(article_text)
        stopwords = nltk.corpus.stopwords.words('english')
        
        word_frequencies = {}
        for word in nltk.word_tokenize(formatted_article_text):
            if word not in stopwords:
                if word not in word_frequencies.keys():
                    word_frequencies[word] = 1
                else:
                    word_frequencies[word] += 1
        maximum_frequency = max(word_frequencies.values())
        for word in word_frequencies.keys():
            word_frequencies[word] = (word_frequencies[word] / maximum_frequency)
        
        sentence_scores = {}
        for sent in sentence_list:
            for word in nltk.word_tokenize(sent.lower()):
                if word in word_frequencies.keys():
                    if len(sent.split(' ')) < 30:
                        if sent not in sentence_scores.keys():
                            sentence_scores[sent] = word_frequencies[word]
                        else:
                            sentence_scores[sent] += word_frequencies[word]
        
        summary_sentences = heapq.nlargest(7, sentence_scores, key=sentence_scores.get)
        summary = ' '.join(summary_sentences)

        # Remove "^" from summary
        summary = summary.replace('^', '')
        summary = summary.replace('"' , '')

        print(f"Summary: {summary}")
        return jsonify({"summary": summary})
    
    except Exception as e:
        error_message = f"Error processing the article: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    app.run(debug=True)
