"""
Frame Detection Service - Detect narrative frames in text
Uses pattern matching and entity analysis to identify framing strategies
"""
import spacy
import re
from typing import List, Dict, Any, Optional
from collections import Counter

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")


class FrameDetectionService:
    """
    Detect narrative frames in text using pattern matching and NLP

    Frame types:
    - victim: Entity portrayed as victim/suffering
    - hero: Entity portrayed as hero/savior
    - threat: Entity portrayed as threat/danger
    - solution: Entity/action portrayed as solution
    - conflict: Conflict/opposition framing
    - economic: Economic impact framing
    """

    # Frame patterns (keywords and phrases)
    FRAME_PATTERNS = {
        "victim": [
            r"\b(suffer|victim|hurt|harmed|damaged|affected|impact|vulnerable|helpless)\b",
            r"\b(crisis|disaster|tragedy|devastation|destruction)\b",
            r"\b(struggle|hardship|difficulty|challenge)\b",
        ],
        "hero": [
            r"\b(hero|savior|rescue|save|help|assist|support|defend|protect)\b",
            r"\b(triumph|success|victory|achievement|accomplish)\b",
            r"\b(brave|courageous|valiant|heroic)\b",
        ],
        "threat": [
            r"\b(threat|danger|risk|menace|peril|hazard)\b",
            r"\b(attack|assault|aggression|hostile|enemy)\b",
            r"\b(fear|terror|alarm|panic|concern)\b",
        ],
        "solution": [
            r"\b(solution|fix|resolve|address|tackle|deal with)\b",
            r"\b(reform|improve|enhance|better|progress)\b",
            r"\b(plan|strategy|initiative|proposal|measure)\b",
        ],
        "conflict": [
            r"\b(conflict|dispute|clash|fight|battle|war)\b",
            r"\b(oppose|against|versus|rivalry|competition)\b",
            r"\b(divide|split|polarize|tension)\b",
        ],
        "economic": [
            r"\b(economy|economic|financial|fiscal|monetary)\b",
            r"\b(market|trade|business|commerce|industry)\b",
            r"\b(cost|price|budget|spending|revenue|profit|loss)\b",
        ],
    }

    def __init__(self):
        self.nlp = nlp

    def detect_frames(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect all narrative frames in text

        Returns:
            List of frame dictionaries with type, confidence, excerpt, entities
        """
        doc = self.nlp(text)
        frames = []

        # Detect each frame type
        for frame_type, patterns in self.FRAME_PATTERNS.items():
            matches = []
            for pattern in patterns:
                matches.extend(re.finditer(pattern, text, re.IGNORECASE))

            if matches:
                # Calculate confidence based on match frequency
                confidence = min(len(matches) / 10.0, 1.0)  # Max at 10 matches

                # Extract entities from sentences containing matches
                entities = self._extract_frame_entities(doc, matches)

                # Get text excerpt around first match
                if matches:
                    match = matches[0]
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    excerpt = text[start:end].strip()
                else:
                    excerpt = None

                frames.append({
                    "frame_type": frame_type,
                    "confidence": confidence,
                    "text_excerpt": excerpt,
                    "entities": entities,
                    "match_count": len(matches),
                })

        # Sort by confidence
        frames.sort(key=lambda x: x["confidence"], reverse=True)
        return frames

    def detect_dominant_frame(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detect the dominant narrative frame in text

        Returns:
            Dictionary with dominant frame info or None
        """
        frames = self.detect_frames(text)
        return frames[0] if frames else None

    def _extract_frame_entities(self, doc, matches) -> Dict[str, List[str]]:
        """Extract entities from sentences containing frame matches"""
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
        }

        # Get sentences containing matches
        match_positions = [m.start() for m in matches]
        relevant_sentences = []
        for sent in doc.sents:
            if any(sent.start_char <= pos < sent.end_char for pos in match_positions):
                relevant_sentences.append(sent)

        # Extract entities from relevant sentences
        for sent in relevant_sentences:
            for ent in sent.ents:
                if ent.label_ == "PERSON":
                    entities["persons"].append(ent.text)
                elif ent.label_ in ("ORG", "NORP"):
                    entities["organizations"].append(ent.text)
                elif ent.label_ in ("GPE", "LOC"):
                    entities["locations"].append(ent.text)

        # Remove duplicates and limit to top 5
        for key in entities:
            entities[key] = list(dict.fromkeys(entities[key]))[:5]

        return entities

    def analyze_framing_evolution(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze how framing changes over multiple texts (e.g., over time)

        Returns:
            Dictionary with framing trends
        """
        frame_counts = Counter()
        frame_confidences = {}

        for text in texts:
            frames = self.detect_frames(text)
            for frame in frames:
                frame_type = frame["frame_type"]
                frame_counts[frame_type] += 1

                if frame_type not in frame_confidences:
                    frame_confidences[frame_type] = []
                frame_confidences[frame_type].append(frame["confidence"])

        # Calculate averages
        trends = {}
        for frame_type, count in frame_counts.items():
            avg_confidence = sum(frame_confidences[frame_type]) / len(frame_confidences[frame_type])
            trends[frame_type] = {
                "count": count,
                "avg_confidence": avg_confidence,
                "percentage": count / len(texts) * 100,
            }

        return {
            "total_texts": len(texts),
            "frame_trends": trends,
            "dominant_frame": max(trends.items(), key=lambda x: x[1]["count"])[0] if trends else None,
        }


# Global service instance
frame_detection_service = FrameDetectionService()
