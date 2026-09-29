from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path
import re

from pypdf import PdfReader


@dataclass(frozen=True)
class Document:
    document_id: str
    version: str
    valid_from: date
    valid_to: date | None
    content: str
    content_hash: str
    source_file: str


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%d.%m.%Y").date()


def read_pdf(path: Path) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_document(path: Path) -> Document:
    text = read_pdf(path)

    # Paragraph and title
    match = re.search(
        r"§\s*([0-9]+a?)\s+SGB\s+VI\s*:",
        text
    )
    if not match:
        raise ValueError(f"Could not identify paragraph in {path}")

    paragraph = match.group(1)

    # Version and validity
    version = re.search(r"Version\s+(\d+\.\d+)", text)
    valid_from = re.search(r"Inkrafttreten\s+(\d{2}\.\d{2}\.\d{4})", text)
    valid_to = re.search(r"Gültig\s+bis\s+(\d{2}\.\d{2}\.\d{4})", text)

    if not version or not valid_from:
        raise ValueError(f"Missing metadata in {path}")

    # Extract the legal text and exclude the document metadata/footer.
    content_match = re.search(
        rf"(§\s*{re.escape(paragraph)}\s+SGB\s+VI:.*?)(?:Literatursystem|\Z)",
        text,
        flags=re.S,
    )

    if not content_match:
        raise ValueError(f"Could not extract legal text from {path}")

    content = content_match.group(1)

    # Normalize whitespace before calculating the hash.
    content = " ".join(content.split())

    content_hash = sha256(
        content.encode("utf-8")
    ).hexdigest()

    return Document(
        document_id=f"sgbvi-{paragraph}",
        version=version.group(1),
        valid_from=parse_date(valid_from.group(1)),
        valid_to=(
            parse_date(valid_to.group(1))
            if valid_to
            else None
        ),
        content=content,
        content_hash=content_hash,
        source_file=path.name,
    )


def load_documents(folder: Path) -> dict[str, Document]:
    """Load one snapshot of the source."""
    documents = {}

    for path in folder.glob("*.pdf"):
        document = parse_document(path)
        documents[document.document_id] = document

    return documents


def detect_changes(
    old: dict[str, Document],
    new: dict[str, Document],
) -> dict[str, list[Document]]:

    added = []
    changed = []
    unchanged = []
    removed = []

    for document_id, new_doc in new.items():

        old_doc = old.get(document_id)

        if old_doc is None:
            added.append(new_doc)

        elif (
            old_doc.content_hash == new_doc.content_hash
            and old_doc.version == new_doc.version
            and old_doc.valid_from == new_doc.valid_from
            and old_doc.valid_to == new_doc.valid_to
        ):
            unchanged.append(new_doc)

        else:
            changed.append(new_doc)

    # Documents that were present in the previous snapshot
    # but are no longer provided by the source.
    for document_id, old_doc in old.items():
        if document_id not in new:
            removed.append(old_doc)

    return {
        "added": added,
        "changed": changed,
        "unchanged": unchanged,
        "removed": removed,
    }


def update_knowledge_base(changes):
    """
    Update the vector database.

    Only new and changed documents need to be
    chunked and embedded again.
    """

    for document in changes["added"]:
        index_document(document)

    for document in changes["changed"]:
        deactivate_old_version(document.document_id)
        index_document(document)

    for document in changes["removed"]:
        deactivate_old_version(document.document_id)


def index_document(document: Document):
    """
    1. Split document into chunks
    2. Create embeddings
    3. Store embeddings + metadata
    """
    pass


def deactivate_old_version(document_id: str):
    """
    Mark the old version as inactive instead of
    physically deleting it.

    This allows historical versions to remain
    available for date-specific queries.
    """
    pass


if __name__ == "__main__":

    old_snapshot = Path("Dateien/SGBVI1-25-057.000.000/")
    new_snapshot = Path("Dateien/SGBVI1-25-057.335.017/")

    old_documents = load_documents(old_snapshot)
    new_documents = load_documents(new_snapshot)

    changes = detect_changes(
        old_documents,
        new_documents,
    )

    for status, documents in changes.items():
        print(f"{status}: {len(documents)}")

    update_knowledge_base(changes)