# Amazon Reviews Sentiment Analysis

This project provides a tool for scraping and analyzing the sentiment of product reviews from Amazon. It leverages the BeautifulSoup library for web scraping, pandas for data manipulation, and Gradio for creating a user-friendly web interface.

## Features

- **Web Scraping**: Extract reviews directly from Amazon product pages.
- **Sentiment Analysis**: Analyze the sentiment of each review using a pre-trained language model.
- **Data Visualization**: Display sentiment analysis results and basic statistics in a Gradio web interface.
- **Filtering by Region**: Specifically retrieve and analyze reviews from Egyptian consumers.

## Installation

To run this project, you will need Python 3.8+ and the following packages:

```bash
pip install pandas gradio bs4 lxml requests
