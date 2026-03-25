"""
Schemas Pydantic pour les articles WordPress.

Valide les donnees entrantes/sortantes des endpoints /social/articles/*.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ════════════════════════════════════════════════════════════════
# TYPES DE BASE
# ════════════════════════════════════════════════════════════════

class WpCategory(BaseModel):
    """Categorie WordPress."""
    id: int
    name: str
    slug: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class WpTag(BaseModel):
    """Tag WordPress."""
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class WpFeaturedMedia(BaseModel):
    """Image mise en avant."""
    id: int
    url: str
    alt: str = ""
    width: int = 0
    height: int = 0

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# ARTICLES
# ════════════════════════════════════════════════════════════════

class ArticleResponse(BaseModel):
    """Article WordPress en reponse."""
    id: int
    site: str
    title: str
    slug: str
    excerpt: str = ""
    content: str = ""
    status: str = "draft"
    author_name: str = ""
    featured_media: Optional[WpFeaturedMedia] = None
    categories: list[WpCategory] = []
    tags: list[WpTag] = []
    link: str = ""
    created_at: str
    updated_at: str
    views: int = 0
    sticky: bool = False

    model_config = ConfigDict(from_attributes=True)


class ArticleListResponse(BaseModel):
    """Reponse paginee de la liste d'articles."""
    items: list[ArticleResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class ArticleCreate(BaseModel):
    """Donnees pour creer un article."""
    title: str = Field(..., min_length=1, max_length=500, description="Titre de l'article")
    content: str = Field(..., min_length=1, description="Contenu HTML de l'article")
    excerpt: Optional[str] = Field(None, max_length=1000, description="Extrait")
    status: str = Field("draft", description="Statut: publish, draft, pending, private")
    categories: list[int] = Field(default=[], description="IDs des categories")
    tags: list[int] = Field(default=[], description="IDs des tags")
    featured_media_id: Optional[int] = Field(None, description="ID de l'image mise en avant")
    sticky: bool = Field(False, description="Epingler l'article en page d'accueil")

    model_config = ConfigDict(from_attributes=True)


class ArticleUpdate(BaseModel):
    """Donnees pour modifier un article (tous les champs optionnels)."""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    excerpt: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    categories: Optional[list[int]] = None
    tags: Optional[list[int]] = None
    featured_media_id: Optional[int] = None
    sticky: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


# ════════════════════════════════════════════════════════════════
# STATISTIQUES
# ════════════════════════════════════════════════════════════════

class ArticleSiteStat(BaseModel):
    site: str
    count: int
    views: int

class ArticleCategoryStat(BaseModel):
    category: str
    count: int

class TopArticle(BaseModel):
    id: int
    site: str
    title: str
    views: int
    link: str

class ArticleStatsResponse(BaseModel):
    total_articles: int
    total_views: int
    articles_this_month: int
    top_articles: list[TopArticle]
    by_site: list[ArticleSiteStat]
    by_category: list[ArticleCategoryStat]


# ════════════════════════════════════════════════════════════════
# GENERATION IA
# ════════════════════════════════════════════════════════════════

class GenerateArticleRequest(BaseModel):
    """Requete pour generer un article depuis des URLs source (articles web ou videos YouTube)."""
    urls: list[str] = Field(..., min_length=1, max_length=3, description="URLs des articles ou videos source (1 a 3)")
    site: str = Field(..., description="Site cible: audacemagazine ou radioaudace")
    mode: str = Field("article_magazine", description="Mode: article_magazine, article_radio, article_libre, article_video")
    custom_instructions: Optional[str] = Field(None, max_length=500, description="Instructions supplementaires")
    subtitle_text: Optional[str] = Field(None, max_length=100000, description="Texte de sous-titres fourni manuellement en complement des URLs (jusqu'a 100k caracteres)")


class GenerateArticleResponse(BaseModel):
    """Reponse avec l'article genere par l'IA."""
    title: str
    content: str
    excerpt: str
    source_urls: list[str]
    has_youtube_sources: bool = Field(False, description="True si au moins une source est une video YouTube")


class GenerateExcerptRequest(BaseModel):
    """Requete pour generer un extrait optimise OG."""
    content: str = Field(..., min_length=20, description="Contenu HTML de l'article")
    site: str = Field("audacemagazine", description="Site cible")
