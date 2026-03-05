"""
Service IA pour la generation de contenu social a partir d'URL.

Utilise Mistral Small 3.2 pour analyser le contenu d'un article web
et generer une publication Facebook adaptee a une radio communautaire.
"""

import re
import html
import logging
from typing import Optional

import httpx
from fastapi import HTTPException, status

from app.config.config import settings

logger = logging.getLogger("hapson-api")

# Timeout pour le fetch d'article
FETCH_TIMEOUT = 15.0
# Limite de caracteres envoyes a Mistral (economiser les tokens)
MAX_ARTICLE_CHARS = 4000


def fetch_article_text(url: str) -> str:
    """
    Telecharge une page web et extrait le texte brut.

    Utilise une approche simple : suppression des balises HTML,
    des scripts/styles, puis nettoyage des espaces.
    Pas de dependance externe (pas de BeautifulSoup).
    """
    try:
        with httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
            response = client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; RadioManager/1.0)"
            })

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Impossible de recuperer l'article (HTTP {response.status_code})"
            )

        html_content = response.text

        # Supprimer scripts, styles, nav, header, footer
        html_content = re.sub(
            r'<(script|style|nav|header|footer)[^>]*>.*?</\1>',
            '', html_content, flags=re.DOTALL | re.IGNORECASE,
        )
        # Supprimer les balises HTML
        text = re.sub(r'<[^>]+>', ' ', html_content)
        # Decoder les entites HTML
        text = html.unescape(text)
        # Nettoyer les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()

        # Tronquer pour economiser les tokens Mistral
        if len(text) > MAX_ARTICLE_CHARS:
            text = text[:MAX_ARTICLE_CHARS] + "..."

        if len(text) < 50:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le contenu de la page est trop court ou inaccessible."
            )

        return text

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout lors de la recuperation de l'article"
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur fetch article {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur reseau lors de la recuperation de l'article"
        )


def generate_post_from_article(article_text: str, url: str, mode: str = "post_engageant", custom_instructions: str | None = None) -> str:
    """
    Genere un post a partir du texte d'un article.

    Utilise Mistral Small via le SDK Python officiel.
    Le prompt est adapte selon le mode choisi et enrichi
    par les instructions supplementaires de l'utilisateur.
    """
    if not settings.MISTRAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service IA non configure (cle API Mistral manquante)"
        )

    # Instructions specifiques selon le mode
    mode_instructions = {
        "post_engageant": (
            "Genere une publication engageante pour les reseaux sociaux.\n"
            "- 2 a 4 phrases maximum, percutantes\n"
            "- Commence par une accroche forte\n"
            "- Termine par un appel a l'action (question, invitation a commenter)\n"
        ),
        "resume": (
            "Resume l'article de maniere claire et concise.\n"
            "- 3 a 5 phrases qui couvrent les points essentiels\n"
            "- Ton informatif et neutre\n"
            "- Structure : contexte, faits cles, conclusion\n"
        ),
        "informatif": (
            "Cree un post informatif et factuel.\n"
            "- Presente les informations cles de l'article\n"
            "- Ton professionnel et serieux\n"
            "- Inclus les chiffres ou donnees importantes si disponibles\n"
            "- Termine par une invitation a lire l'article complet\n"
        ),
        "annonce": (
            "Cree une annonce percutante pour partager cette nouvelle.\n"
            "- Commence par une phrase d'accroche forte\n"
            "- Ton enthousiaste et dynamique\n"
            "- 2 a 3 phrases courtes et impactantes\n"
            "- Termine par un appel a l'action clair\n"
        ),
    }

    mode_text = mode_instructions.get(mode, mode_instructions["post_engageant"])

    system_prompt = (
        "Tu es le community manager d'une radio communautaire francophone. "
        "Ton role est de creer des publications pour les reseaux sociaux a partir d'articles web. "
        "Regles generales :\n"
        "- Ecris en francais, ton amical et accessible\n"
        "- N'inclus PAS de hashtags (ils seront ajoutes separement)\n"
        "- N'inclus PAS l'URL (elle sera ajoutee automatiquement)\n"
        "- Adapte le ton selon le sujet (info locale, culture, musique, evenement...)\n"
        "\n"
        "Mode de generation :\n"
        f"{mode_text}"
    )

    if custom_instructions and custom_instructions.strip():
        system_prompt += (
            "\nInstructions supplementaires de l'utilisateur :\n"
            f"{custom_instructions.strip()}\n"
        )

    user_prompt = (
        f"Voici le contenu d'un article web :\n\n"
        f"{article_text}\n\n"
        f"URL source : {url}\n\n"
        f"Genere une publication Facebook courte et engageante pour notre page de radio communautaire."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        # SDK v1.x : from mistralai import Mistral
        # SDK v0.x : from mistralai.client import MistralClient
        try:
            from mistralai import Mistral
            client = Mistral(api_key=settings.MISTRAL_API_KEY)
            response = client.chat.complete(
                model="mistral-small-latest",
                messages=messages,
                max_tokens=300,
                temperature=0.7,
            )
        except ImportError:
            from mistralai.client import MistralClient
            from mistralai.models.chat_completion import ChatMessage
            client = MistralClient(api_key=settings.MISTRAL_API_KEY)
            response = client.chat(
                model="mistral-small-latest",
                messages=[ChatMessage(role=m["role"], content=m["content"]) for m in messages],
                max_tokens=300,
                temperature=0.7,
            )

        generated = response.choices[0].message.content.strip()

        if not generated:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="L'IA n'a pas genere de contenu"
            )

        logger.info(f"Post IA genere ({len(generated)} chars) pour URL: {url}")
        return generated

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur Mistral API: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur lors de la generation IA : {str(e)}"
        )
