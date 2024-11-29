from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import SpeechtoText  

def analyze_sentiment(transcription):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_score = analyzer.polarity_scores(transcription)
    compound_score = sentiment_score['compound']
    if compound_score >= 0.05:
        sentiment = "Positive"
    elif compound_score <= -0.05:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
    return sentiment, compound_score

def main():
    transcript_sentences = []
    try:
        transcription = SpeechtoText.record_speech()
        if transcription:
            print(f"Transcription result: {transcription}")
            transcript_sentences = transcription.split(".")
            for i in transcript_sentences:
                sentiment, score = analyze_sentiment(i)
                print("i")
                print(f"Sentiment: {sentiment}")
                print(f"Compound Sentiment Score: {score}")
                print("----------------------------------")
        else:
            print("No transcription was returned.")

    except Exception as e:
        print(f"Error during transcription or sentiment analysis: {e}")


if __name__ == "__main__":
    main()
