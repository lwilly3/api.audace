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


# ════════════════════════════════════════════════════════════════
# GENERATION D'ARTICLES WORDPRESS
# ════════════════════════════════════════════════════════════════

# Limite de caracteres par source pour les articles (plus genereux que les posts)
MAX_ARTICLE_SOURCE_CHARS = 6000


def _strip_html_simple(html_text: str) -> str:
    """Retire les balises HTML pour obtenir du texte brut."""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def _call_mistral(messages: list[dict], max_tokens: int = 300, temperature: float = 0.7) -> str:
    """Appelle l'API Mistral et retourne le texte genere."""
    if not settings.MISTRAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service IA non configure (cle API Mistral manquante)"
        )

    try:
        try:
            from mistralai import Mistral
            client = Mistral(api_key=settings.MISTRAL_API_KEY)
            response = client.chat.complete(
                model="mistral-small-latest",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except ImportError:
            from mistralai.client import MistralClient
            from mistralai.models.chat_completion import ChatMessage
            client = MistralClient(api_key=settings.MISTRAL_API_KEY)
            response = client.chat(
                model="mistral-small-latest",
                messages=[ChatMessage(role=m["role"], content=m["content"]) for m in messages],
                max_tokens=max_tokens,
                temperature=temperature,
            )

        generated = response.choices[0].message.content.strip()
        if not generated:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="L'IA n'a pas genere de contenu"
            )
        return generated

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur Mistral API: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur lors de la generation IA : {str(e)}"
        )


def generate_article_from_urls(
    urls: list[str],
    site_key: str,
    mode: str = "article_magazine",
    custom_instructions: str | None = None,
) -> dict:
    """
    Genere un article HTML complet a partir d'une ou plusieurs URLs source.

    Retourne un dict avec title, content, excerpt.
    """
    # Extraire le texte de chaque URL (max 3)
    sources = []
    for url in urls[:3]:
        try:
            text = fetch_article_text(url)
            # Augmenter la limite pour les articles
            if len(text) > MAX_ARTICLE_SOURCE_CHARS:
                text = text[:MAX_ARTICLE_SOURCE_CHARS] + "..."
            sources.append({"url": url, "text": text})
        except Exception as e:
            logger.warning(f"Impossible d'extraire {url}: {e}")
            continue

    if not sources:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Aucune des URLs fournies n'a pu etre lue"
        )

    # Construire le contexte des sources
    sources_text = ""
    for i, src in enumerate(sources, 1):
        sources_text += f"\n--- Source {i} ({src['url']}) ---\n{src['text']}\n"

    # Prompts selon le mode
    mode_instructions = {
        "article_magazine": (
            "Redige un article de style MAGAZINE.\n"
            "- Ton editorial, soigne et professionnel\n"
            "- Structure claire : introduction captivante, developpement en sections avec sous-titres, conclusion\n"
            "- Utilise du HTML : <h2> pour les sous-titres, <p> pour les paragraphes, <strong> pour les points importants, <blockquote> pour les citations\n"
            "- Minimum 4-6 paragraphes riches et detailles\n"
            "- Style Audace Magazine : culturel, engageant, mediatique\n"
        ),
        "article_radio": (
            "Redige un article de style INFO RADIO / WEB.\n"
            "- Ton direct, accessible et informatif\n"
            "- Structure web : chapeau accrocheur, paragraphes courts, faits essentiels en premier\n"
            "- Utilise du HTML : <h2> pour les sous-titres, <p> pour les paragraphes, <strong> pour les chiffres et noms importants\n"
            "- Format pyramide inversee : les infos les plus importantes d'abord\n"
            "- Style Radio Audace : dynamique, proche de l'auditeur, communautaire\n"
        ),
        "article_libre": (
            "Redige un article web de qualite.\n"
            "- Ton neutre et professionnel\n"
            "- Utilise du HTML : <h2> pour les sous-titres, <p> pour les paragraphes\n"
            "- Structure libre adaptee au sujet\n"
            "- L'utilisateur guidera le style via ses instructions\n"
        ),
    }

    mode_text = mode_instructions.get(mode, mode_instructions["article_magazine"])

    system_prompt = (
        "Tu es un redacteur web professionnel francophone. "
        "Tu rediges des articles pour des sites web WordPress. "
        "Regles generales :\n"
        "- Ecris en francais correct et fluide\n"
        "- Genere du HTML propre et semantique (pas de <html>, <body>, juste le contenu)\n"
        "- Propose un titre accrocheur (non HTML, texte brut) sur la premiere ligne, precede de 'TITRE: '\n"
        "- Apres le titre, le contenu HTML commence\n"
        "- Ne copie pas mot a mot les sources, reformule et enrichis\n"
        "- Cite les sources si pertinent\n"
        "\nStyle d'ecriture :\n"
        f"{mode_text}"
    )

    if custom_instructions and custom_instructions.strip():
        system_prompt += (
            "\nInstructions supplementaires de l'utilisateur :\n"
            f"{custom_instructions.strip()}\n"
        )

    user_prompt = (
        "Voici les sources a partir desquelles rediger l'article :\n"
        f"{sources_text}\n\n"
        "Genere un article complet. Commence par 'TITRE: ' suivi du titre, "
        "puis le contenu HTML de l'article."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    generated = _call_mistral(messages, max_tokens=2000, temperature=0.7)

    # Parser le resultat : extraire le titre et le contenu
    title = ""
    content = generated

    lines = generated.split("\n", 1)
    if lines[0].upper().startswith("TITRE:"):
        title = lines[0].replace("TITRE:", "").replace("Titre:", "").strip().strip("\"'")
        content = lines[1].strip() if len(lines) > 1 else ""

    # Generer aussi un extrait automatiquement
    excerpt = generate_article_excerpt(content, site_key)

    logger.info(f"Article IA genere ({len(content)} chars) depuis {len(sources)} source(s)")

    return {
        "title": title,
        "content": content,
        "excerpt": excerpt,
        "source_urls": [s["url"] for s in sources],
    }


def generate_article_excerpt(content: str, site_key: str = "audacemagazine") -> str:
    """
    Genere un extrait optimise pour les aperçus Open Graph (WhatsApp, Facebook, LinkedIn).

    L'extrait doit faire 150-160 caracteres, etre une phrase complete
    et donner envie de cliquer.
    """
    # Nettoyer le HTML pour envoyer du texte brut a Mistral
    plain_text = _strip_html_simple(content)
    if len(plain_text) > 2000:
        plain_text = plain_text[:2000] + "..."

    if len(plain_text) < 20:
        return ""

    site_context = {
        "audacemagazine": "un magazine web culturel et mediatique (Audace Magazine)",
        "radioaudace": "un site d'information d'une radio communautaire (Radio Audace)",
    }
    site_desc = site_context.get(site_key, "un site web d'information")

    system_prompt = (
        "Tu es un expert en SEO et reseaux sociaux. "
        f"Tu travailles pour {site_desc}. "
        "Genere un extrait (meta description) optimise pour les aperçus de partage "
        "(Open Graph : WhatsApp, Facebook, LinkedIn, Twitter).\n"
        "Regles strictes :\n"
        "- Exactement 150 a 160 caracteres (espaces compris)\n"
        "- UNE phrase complete, informative et accrocheuse\n"
        "- Pas de hashtags, pas d'emojis, pas de guillemets\n"
        "- Donne envie de cliquer et lire l'article\n"
        "- Reponds UNIQUEMENT avec l'extrait, rien d'autre\n"
    )

    user_prompt = (
        f"Voici le contenu de l'article :\n\n{plain_text}\n\n"
        "Genere l'extrait optimise (150-160 caracteres)."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    excerpt = _call_mistral(messages, max_tokens=80, temperature=0.5)

    # Nettoyer : retirer les guillemets eventuels
    excerpt = excerpt.strip("\"'«»")

    logger.info(f"Extrait IA genere ({len(excerpt)} chars) pour site {site_key}")
    return excerpt
