import io
import logging
import re

logger = logging.getLogger(__name__)


def parse_resume(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        return _parse_pdf(file_bytes)
    elif ext == "docx":
        return _parse_docx(file_bytes)
    else:
        return _parse_text(file_bytes)


def _parse_pdf(file_bytes: bytes) -> str:
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except ImportError:
        logger.warning("pymupdf not installed, using fallback text extraction")
        return _parse_text(file_bytes)
    except Exception as e:
        logger.error("PDF parsing failed: %s", e)
        return _parse_text(file_bytes)


def _parse_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        logger.warning("python-docx not installed, using fallback text extraction")
        return _parse_text(file_bytes)
    except Exception as e:
        logger.error("DOCX parsing failed: %s", e)
        return _parse_text(file_bytes)


def _parse_text(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8", errors="replace")
    except Exception:
        return file_bytes.decode("latin-1", errors="replace")


def extract_work_experience(text: str) -> list[dict]:
    experiences = []
    lines = text.split("\n")
    current_role = {}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        role_match = re.match(
            r"(.+?)\s+(?:at|@)\s+(.+?)(?:\s*[|–-]\s*(.+))?$",
            stripped, re.IGNORECASE
        )
        if role_match:
            if current_role.get("title"):
                experiences.append(current_role)
            current_role = {"title": role_match.group(1).strip(), "company": role_match.group(2).strip()}
        elif current_role:
            current_role.setdefault("details", []).append(stripped)
    if current_role.get("title"):
        experiences.append(current_role)
    return experiences


def extract_technologies(text: str) -> list[str]:
    tech_patterns = [
        r"\b(React|Angular|Vue|Svelte|Next\.?js|Nuxt|Gatsby)\b",
        r"\b(Python|JavaScript|TypeScript|Rust|Go|Java|Kotlin|Swift|C\+\+|C#|Ruby|PHP|Scala)\b",
        r"\b(Node\.?js|Deno|Bun|Express|FastAPI|Django|Flask|Spring|Rails|Laravel)\b",
        r"\b(PostgreSQL|MySQL|SQLite|MongoDB|Redis|DynamoDB|Cassandra|Elasticsearch)\b",
        r"\b(Docker|Kubernetes|Terraform|Ansible|CI/CD|Jenkins|GitHub Actions)\b",
        r"\b(AWS|GCP|Azure|Cloud|Lambda|S3|EC2|ECS|Fargate)\b",
        r"\b(GraphQL|REST|gRPC|WebSocket|tRPC)\b",
        r"\b(Redux|Zustand|Jotai|Recoil|MobX|TanStack Query|React Query)\b",
        r"\b(Tailwind|Styled Components|CSS-in-JS|Sass|Less)\b",
        r"\b(Jest|Vitest|Cypress|Playwright|Testing Library|Selenium)\b",
    ]
    technologies = set()
    for pattern in tech_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            technologies.add(match.group(0))
    return sorted(technologies)


def extract_projects(text: str) -> list[dict]:
    projects = []
    lines = text.split("\n")
    in_project = False
    current_project = {}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_project:
                projects.append(current_project)
                current_project = {}
                in_project = False
            continue
        project_match = re.match(r"(?:Project|Side|Personal)?\s*:?\s*(.+?)(?:\s*[|–-]\s*(.+))?$", stripped, re.IGNORECASE)
        if re.match(r"^(Project|Side Project|Personal Project)", stripped, re.IGNORECASE) and not in_project:
            in_project = True
            current_project = {"name": stripped.split(":", 1)[-1].strip() if ":" in stripped else stripped}
        elif in_project:
            current_project.setdefault("details", []).append(stripped)
    if current_project:
        projects.append(current_project)
    return projects


def extract_education(text: str) -> list[dict]:
    education = []
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()
        if re.search(r"(B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|PhD|Bachelor|Master|Doctorate|B\.?Tech|M\.?Tech)", stripped, re.IGNORECASE):
            education.append({"text": stripped})
    return education


def extract_quantified_achievements(text: str) -> list[str]:
    achievements = []
    patterns = [
        r"(?:improved|increased|reduced|decreased|boosted|optimized|cut|grew|accelerated)\s+[\w\s]+?\s+(?:by\s+)?\d+[\d.%]*",
        r"(?:led|managed|mentored|supervised)\s+(?:a\s+)?(?:team\s+of\s+)?\d+",
        r"(?:delivered|shipped|launched|built|developed)\s+[\w\s]+?\s+(?:for|serving|used\s+by)\s+\d+[\d+,]*",
        r"\d+[\d+,]*\s+(?:users|customers|clients|requests|queries|transactions)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            achievements.append(match.group(0).strip())
    return achievements


def extract_leadership_signals(text: str) -> list[str]:
    signals = []
    keywords = [
        "led", "lead", "managed", "mentored", "head of", "director",
        "principal", "staff", "architect", "owner", "ownership",
        "team lead", "tech lead", "initiative", "drove", "spearheaded",
    ]
    for keyword in keywords:
        matches = re.finditer(rf"[^.]*\b{keyword}\b[^.]*\.", text, re.IGNORECASE)
        for match in matches:
            signals.append(match.group(0).strip())
    return signals
