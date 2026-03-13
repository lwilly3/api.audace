"""
Service IA pour la generation de contenu social a partir d'URL.

Utilise Mistral Small 3.2 pour analyser le contenu d'un article web
ou la transcription d'une video YouTube, et generer une publication
adaptee a une radio communautaire.
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
# Limite de caracteres pour les transcriptions YouTube (plus genereux car contenu dense)
MAX_YOUTUBE_TRANSCRIPT_CHARS = 8000

# Pattern pour detecter les URLs YouTube
YOUTUBE_URL_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|embed/|v/)|youtu\.be/)([\w-]{11})',
    re.IGNORECASE,
)


def is_youtube_url(url: str) -> bool:
    """Detecte si une URL est une URL YouTube."""
    return bool(YOUTUBE_URL_PATTERN.search(url))


def extract_youtube_video_id(url: str) -> str | None:
    """Extrait l'ID video (11 caracteres) d'une URL YouTube."""
    match = YOUTUBE_URL_PATTERN.search(url)
    return match.group(1) if match else None


def fetch_youtube_transcript(url: str) -> dict:
    """
    Extrait les sous-titres d'une video YouTube via le Cloudflare Worker.

    Le Worker extrait les sous-titres depuis YouTube (pas de blocage IP cloud).
    L'endpoint oEmbed est utilise en complement pour le titre et l'auteur.
    Retourne un dict avec video_id, title, author, language, transcript_text, thumbnail_url.
    """
    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="URL YouTube invalide ou ID video introuvable"
        )

    worker_url = settings.YOUTUBE_WORKER_URL
    if not worker_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service d'extraction YouTube n'est pas configure (YOUTUBE_WORKER_URL manquant)"
        )

    # Recuperer le titre et l'auteur via oEmbed (pas de cle API necessaire)
    title = ""
    author = ""
    try:
        with httpx.Client(timeout=10.0) as client:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            resp = client.get(oembed_url)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", "")
                author = data.get("author_name", "")
    except Exception as e:
        logger.warning(f"Impossible de recuperer les metadonnees oEmbed pour {video_id}: {e}")

    # Appeler le Cloudflare Worker pour extraire les sous-titres
    try:
        headers = {}
        if settings.YOUTUBE_WORKER_SECRET:
            headers["X-Worker-Secret"] = settings.YOUTUBE_WORKER_SECRET

        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                worker_url,
                params={"video_id": video_id, "lang": "fr"},
                headers=headers,
            )

        if resp.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=resp.json().get("error", "Aucun sous-titre disponible pour cette video")
            )
        if resp.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Video privee ou soumise a une restriction d'age"
            )
        if resp.status_code != 200:
            error_msg = "Erreur lors de l'extraction des sous-titres YouTube"
            try:
                error_msg = resp.json().get("error", error_msg)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_msg
            )

        worker_data = resp.json()
        transcript_text = worker_data.get("full_text", "")
        language = worker_data.get("language", "fr")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur appel Worker YouTube pour {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur lors de l'extraction des sous-titres YouTube"
        )

    # Nettoyer et tronquer
    transcript_text = re.sub(r'\s+', ' ', transcript_text).strip()
    if len(transcript_text) > MAX_YOUTUBE_TRANSCRIPT_CHARS:
        transcript_text = transcript_text[:MAX_YOUTUBE_TRANSCRIPT_CHARS] + "..."

    if len(transcript_text) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La transcription de la video est trop courte"
        )

    logger.info(f"Transcription YouTube extraite ({len(transcript_text)} chars) pour video {video_id}")

    return {
        "video_id": video_id,
        "title": title,
        "author": author,
        "language": language,
        "transcript_text": transcript_text,
        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
    }


def fetch_content_from_url(url: str) -> dict:
    """
    Dispatcher : detecte le type d'URL et extrait le contenu.

    Retourne un dict uniforme :
      - source_type: 'article' | 'youtube'
      - text: le texte extrait
      - metadata: dict de metadonnees (vide pour les articles, riche pour YouTube)
    """
    if is_youtube_url(url):
        yt_data = fetch_youtube_transcript(url)
        return {
            "source_type": "youtube",
            "text": yt_data["transcript_text"],
            "metadata": {
                "video_id": yt_data["video_id"],
                "title": yt_data["title"],
                "author": yt_data["author"],
                "language": yt_data["language"],
                "thumbnail_url": yt_data["thumbnail_url"],
            },
        }
    else:
        text = fetch_article_text(url)
        return {
            "source_type": "article",
            "text": text,
            "metadata": {},
        }


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


def generate_post_from_article(article_text: str, url: str, mode: str = "post_engageant", custom_instructions: str | None = None, source_type: str = "article") -> str:
    """
    Genere un post a partir du texte d'un article ou d'une transcription YouTube.

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
        "resume_video": (
            "Resume les points cles de cette video YouTube.\n"
            "- 3 a 5 phrases couvrant les moments importants\n"
            "- Mentionne qu'il s'agit d'une video\n"
            "- Ton enthousiaste, invite a regarder la video\n"
        ),
        "points_cles": (
            "Extrais les points cles de cette video YouTube.\n"
            "- Sous forme de liste a puces (3 a 6 points)\n"
            "- Chaque point en 1 phrase concise\n"
            "- Commence par une phrase d'introduction\n"
            "- Termine par un appel a regarder la video complete\n"
        ),
    }

    mode_text = mode_instructions.get(mode, mode_instructions["post_engageant"])

    system_prompt = (
        "Tu es le community manager d'une radio communautaire francophone. "
        "Ton role est de creer des publications pour les reseaux sociaux "
        "a partir " + ("de videos YouTube" if source_type == "youtube" else "d'articles web") + ". "
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

    if source_type == "youtube":
        user_prompt = (
            f"Voici la transcription d'une video YouTube :\n\n"
            f"{article_text}\n\n"
            f"URL de la video : {url}\n\n"
            f"Genere une publication courte et engageante pour notre page de radio communautaire."
        )
    else:
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
    has_youtube = False
    for url in urls[:3]:
        try:
            content_data = fetch_content_from_url(url)
            text = content_data["text"]
            # Augmenter la limite pour les articles
            if len(text) > MAX_ARTICLE_SOURCE_CHARS:
                text = text[:MAX_ARTICLE_SOURCE_CHARS] + "..."
            source_entry = {"url": url, "text": text, "source_type": content_data["source_type"]}
            if content_data["source_type"] == "youtube":
                has_youtube = True
                meta = content_data["metadata"]
                if meta.get("title"):
                    source_entry["yt_title"] = meta["title"]
            sources.append(source_entry)
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
        if src.get("source_type") == "youtube":
            label = f"Video YouTube"
            if src.get("yt_title"):
                label += f" : {src['yt_title']}"
            sources_text += f"\n--- Source {i} — {label} ({src['url']}) ---\n{src['text']}\n"
        else:
            sources_text += f"\n--- Source {i} — Article ({src['url']}) ---\n{src['text']}\n"

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
        "article_video": (
            "Redige un article base sur le contenu d'une ou plusieurs videos YouTube.\n"
            "- Transforme la transcription en article structure et lisible\n"
            "- Utilise du HTML : <h2> pour les sous-titres, <p> pour les paragraphes, <strong> pour les points importants, <blockquote> pour les citations marquantes\n"
            "- Ajoute du contexte et reformule les propos oraux en style ecrit\n"
            "- Minimum 4-6 paragraphes riches\n"
            "- Mentionne que le contenu est tire d'une video\n"
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
        "has_youtube_sources": has_youtube,
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


# ════════════════════════════════════════════════════════════════
# AMELIORATION DE TEXTE EXISTANT
# ════════════════════════════════════════════════════════════════

# Limite de caracteres pour les textes a ameliorer
MAX_IMPROVE_CHARS = 8000


def improve_text(
    text: str,
    content_type: str = "post",
    action: str = "correct",
) -> dict:
    """
    Ameliore un texte existant via Mistral.

    Actions :
    - correct : corrige l'orthographe et la grammaire
    - improve : ameliore la mise en page et la presentation
    - generate_title : genere un titre a partir du contenu

    content_type : 'post' (texte brut) ou 'article' (HTML)
    """
    if not text or len(text.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le texte est trop court pour etre ameliore"
        )

    # Preparer le texte
    input_text = text.strip()
    if len(input_text) > MAX_IMPROVE_CHARS:
        input_text = input_text[:MAX_IMPROVE_CHARS] + "..."

    is_html = content_type == "article"

    if action == "correct":
        result = _improve_correct(input_text, is_html)
    elif action == "improve":
        result = _improve_layout(input_text, is_html)
    elif action == "generate_title":
        result = _improve_generate_title(input_text, is_html)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Action invalide: {action}"
        )

    logger.info(f"Texte ameliore ({action}, {content_type}, {len(result)} chars)")

    return {
        "result": result,
        "action": action,
        "content_type": content_type,
    }


def _improve_correct(text: str, is_html: bool) -> str:
    """Corrige l'orthographe et la grammaire du texte."""
    html_instruction = (
        "Le contenu est en HTML. Conserve toutes les balises HTML intactes. "
        "Ne modifie que le texte entre les balises."
    ) if is_html else (
        "Le contenu est du texte brut (publication pour reseaux sociaux). "
        "Conserve le formatage (sauts de ligne, emojis, hashtags)."
    )

    system_prompt = (
        "Tu es un correcteur professionnel francophone. "
        "Corrige uniquement les fautes d'orthographe, de grammaire, de conjugaison et de ponctuation. "
        "NE MODIFIE PAS le sens, le ton, le style ou la structure du texte. "
        f"{html_instruction}\n"
        "Reponds UNIQUEMENT avec le texte corrige, sans explication ni commentaire."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]

    max_tokens = 1500 if is_html else 500
    return _call_mistral(messages, max_tokens=max_tokens, temperature=0.3)


def _improve_layout(text: str, is_html: bool) -> str:
    """Ameliore la mise en page et la presentation du texte."""
    if is_html:
        html_instruction = (
            "Le contenu est en HTML pour un article WordPress. Ameliore :\n"
            "- La structure HTML : utilise <h2>, <h3> pour les sous-titres, <p> pour les paragraphes\n"
            "- Ajoute des <strong> pour les points importants\n"
            "- Ajoute des <blockquote> pour les citations si pertinent\n"
            "- Ameliore le decoupage en paragraphes et la fluidite\n"
            "- Conserve le sens et les informations du texte original\n"
            "Reponds UNIQUEMENT avec le contenu HTML ameliore."
        )
    else:
        html_instruction = (
            "Le contenu est une publication pour reseaux sociaux (texte brut). Ameliore :\n"
            "- L'accroche (premiere phrase percutante)\n"
            "- La structure (paragraphes courts, listes si pertinent)\n"
            "- L'appel a l'action en fin de publication\n"
            "- Conserve le sens et le ton original\n"
            "- Conserve les emojis et hashtags existants\n"
            "Reponds UNIQUEMENT avec le texte ameliore."
        )

    system_prompt = (
        "Tu es un redacteur web professionnel francophone. "
        "Ameliore la presentation et la mise en page du texte suivant, "
        "tout en preservant le contenu et le sens original.\n"
        f"{html_instruction}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]

    max_tokens = 2000 if is_html else 500
    return _call_mistral(messages, max_tokens=max_tokens, temperature=0.6)


def _improve_generate_title(text: str, is_html: bool) -> str:
    """Genere un titre accrocheur a partir du contenu."""
    # Pour les articles HTML, extraire le texte brut pour l'analyse
    plain_text = _strip_html_simple(text) if is_html else text
    if len(plain_text) > 2000:
        plain_text = plain_text[:2000] + "..."

    system_prompt = (
        "Tu es un redacteur web professionnel francophone specialise en titraille. "
        "Genere UN titre accrocheur, informatif et optimise SEO pour le contenu suivant.\n"
        "Regles :\n"
        "- Maximum 80 caracteres\n"
        "- Pas de guillemets, pas de ponctuation finale\n"
        "- Donne envie de lire\n"
        "- Reponds UNIQUEMENT avec le titre, rien d'autre"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": plain_text},
    ]

    title = _call_mistral(messages, max_tokens=60, temperature=0.7)
    # Nettoyer les guillemets eventuels
    return title.strip("\"'«»")
