"""Text and metadata prepared for the fault-card collection."""

from shipdiag.ontology import COMPONENT_NAMES


def fault_embed_text(card):
    """Join the name, symptoms, cause, and Japanese component names."""
    names = [COMPONENT_NAMES[component] for component in card["components"]]
    return "\n".join([card["name"], card["symptoms"], card["cause"], " ".join(names)])


def fault_metadata(card):
    """Chroma metadata. List fields are comma-separated strings."""
    return {
        "id": card["id"],
        "role": card["role"],
        "systems": card["systems"],
        "severity": card["severity"],
        "components": ",".join(card["components"]),
        "triggers": ",".join(card["triggers"]),
        "derived": ",".join(card["derived"]),
    }
