"""
Workers package for background RabbitMQ consumers.
"""
from .analysis_consumer import AnalysisConsumer
from .article_consumer import ArticleScrapedConsumer

__all__ = ["AnalysisConsumer", "ArticleScrapedConsumer"]
