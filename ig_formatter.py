"""
QUALIA Instagram Formatter — Carousel, Caption & Reels Script Generator
=========================================================================
The "output mouth" of QUALIA — takes raw intel from the NorCal data layer
and QUALIA's LLM responses and formats them into Instagram-native content.

Every piece of content follows the Instagram-first UX principle from The Daily Dig
blueprint: scannable, action-oriented, emoji-punctuated, with a clear CTA and
hashtag block. The formatter knows the difference between a carousel slide
(max ~80 characters per line), a caption post (richer, up to ~2200 chars),
and a Reels script (spoken word, conversational, no visual formatting).

Three primary output types:
  1. CAROUSEL  — 5–10 slide scripts with hook → body → CTA arc
  2. CAPTION   — Single-post caption for feed posts
  3. REELS     — 30–60 second spoken script with visual direction notes
"""

from dataclasses import dataclass, field
from typing import List, Optional
from volley.norcal_intel import VolleyEvent, VolleyEventType, SkillLevel


# ---------------------------------------------------------------------------
# Instagram content primitives
# ---------------------------------------------------------------------------

@dataclass
class CarouselSlide:
    """One slide in an Instagram carousel. Think of it like a flashcard."""
    slide_number: int
    headline: str           # Large bold text — the thing your eye catches first
    body_lines: List[str]   # 2–4 lines of supporting detail
    emoji_accent: str = "🏐"    # Visual anchor emoji for the slide
    is_cover: bool = False      # True for slide 1 (the preview people see in feed)
    cta: Optional[str] = None   # Only on the final slide

    def render(self) -> str:
        """Return a text mockup of the slide for review/preview."""
        lines = [f"── SLIDE {self.slide_number} {'(Cover)' if self.is_cover else ''} ──"]
        lines.append(f"{self.emoji_accent} {self.headline}")
        lines.extend([f"  {line}" for line in self.body_lines])
        if self.cta:
            lines.append(f"\n  👉 {self.cta}")
        return "\n".join(lines)


@dataclass
class IgCarousel:
    """
    A complete Instagram carousel post.
    Best practice: 5–7 slides. Slide 1 = hook, Slides 2-N-1 = value, Slide N = CTA.
    The caption goes with the post itself (not a slide) and should amplify the hook.
    """
    title: str
    slides: List[CarouselSlide] = field(default_factory=list)
    caption: str = ""
    hashtags: List[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"═══ CAROUSEL: {self.title} ═══\n"]
        for slide in self.slides:
            lines.append(slide.render())
            lines.append("")
        lines.append(f"── CAPTION ──\n{self.caption}")
        lines.append(f"\n── HASHTAGS ──\n{' '.join(self.hashtags)}")
        return "\n".join(lines)


@dataclass
class ReelsScript:
    """
    A 30–60 second Instagram Reels script.
    Structure: HOOK (0-3s) → PROOF (3-10s) → VALUE DELIVER (10-50s) → CTA (50-60s)
    """
    title: str
    hook_line: str           # The very first spoken sentence — determines if anyone watches
    sections: List[dict]     # [{"label": "Proof", "script": "...", "visual": "..."}]
    cta_line: str
    estimated_duration_sec: int = 45

    def render(self) -> str:
        lines = [f"═══ REELS SCRIPT: {self.title} ═══",
                 f"⏱ Estimated duration: ~{self.estimated_duration_sec}s\n",
                 f"[HOOK — 0-3s]\n🎙 \"{self.hook_line}\"\n"]
        for sec in self.sections:
            lines.append(f"[{sec['label']}]")
            lines.append(f"🎙 {sec['script']}")
            if sec.get("visual"):
                lines.append(f"📷 Visual: {sec['visual']}")
            lines.append("")
        lines.append(f"[CTA]\n🎙 \"{self.cta_line}\"")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# The Instagram Formatter Engine
# ---------------------------------------------------------------------------

class IgFormatter:
    """
    Transforms QUALIA intel into Instagram-native content formats.
    Called by the agent after it has gathered and verified volleyball intel,
    when the user (or automation) has asked for IG-formatted output.
    """

    # Shared NorCal volleyball hashtag bank — mix high-volume with niche
    CORE_HASHTAGS = [
        "#NorCalVolleyball", "#BayAreaVolleyball", "#SFVolleyball",
        "#NorCalVolleyIntel", "#TheDailyDig", "#VolleyballCommunity",
        "#IndoorVolleyball", "#OpenGym", "#VolleyballLife",
    ]

    LOCATION_HASHTAGS = {
        "San Francisco": ["#SFRec", "#SanFranciscoSports", "#SOMA"],
        "Oakland":       ["#OaklandSports", "#EastBayVolleyball"],
        "San Jose":      ["#SJVolleyball", "#SiliconValleySports", "#SouthBayVolleyball"],
        "Berkeley":      ["#BerkeleyRec", "#EastBayAthletics"],
        "Santa Cruz":    ["#SantaCruzBeach", "#BeachVolleyball"],
    }

    EVENT_HASHTAGS = {
        "open_gym":    ["#DropIn", "#PickupVolleyball", "#OpenGym"],
        "tournament":  ["#VolleyballTournament", "#IndoorTournament", "#CompeteNorCal"],
        "league":      ["#VolleyballLeague", "#AdultLeague", "#TeamSports"],
        "beach":       ["#BeachVolleyball", "#SandVolleyball", "#AVP"],
    }

    # ---------- Carousel Builders ----------

    def events_carousel(self, events: List[VolleyEvent], header_city: Optional[str] = None) -> IgCarousel:
        """
        Build a 'This Week's Open Gyms' style carousel from a list of events.
        Slide 1: Hook/cover. Slides 2-N: one event each. Last slide: CTA.
        """
        city_label = header_city or "NorCal"
        slides = []

        # Slide 1: Cover / Hook
        slides.append(CarouselSlide(
            slide_number=1,
            headline=f"🏐 {city_label} Volleyball Intel",
            body_lines=[
                "Open gyms · Leagues · Tournaments",
                f"{len(events)} verified spots this week →",
                "Swipe to see all ▶",
            ],
            emoji_accent="🏐",
            is_cover=True,
        ))

        # Slides 2–N: one event per slide
        for i, event in enumerate(events[:7], start=2):
            level = event.skill_level.value.replace("_", " ").title()
            status = "✅" if event.verified else "⚠️"
            body = [
                f"📍 {event.venue_name}",
                f"📅 {event.day_of_week or event.start_date or 'See details'} @ {event.start_time or 'TBD'}",
                f"🎯 {level} · {event.gender.title()}",
                f"💰 {event.cost or 'Contact organizer'}",
            ]
            if not event.verified:
                body.append("⚠️ Community-reported — verify before going")

            slides.append(CarouselSlide(
                slide_number=i,
                headline=f"{status} {event.name}",
                body_lines=body,
            ))

        # Last slide: CTA
        slides.append(CarouselSlide(
            slide_number=len(slides) + 1,
            headline="Want More Intel?",
            body_lines=[
                "DM us your city + skill level",
                "We dig up the best spots in NorCal",
                "New intel every week 📲",
            ],
            cta="DM 'OPEN GYM [YOUR CITY]' to get started",
        ))

        # Build hashtag list
        tags = self.CORE_HASHTAGS[:]
        if header_city and header_city in self.LOCATION_HASHTAGS:
            tags += self.LOCATION_HASHTAGS[header_city]
        event_types = {e.event_type.value for e in events}
        for et in event_types:
            tags += self.EVENT_HASHTAGS.get(et, [])

        caption = (
            f"🏐 Your {city_label} volleyball intel drop is HERE. "
            f"Swipe for {len(events)} open gym{' & tournament' if any(e.event_type == VolleyEventType.TOURNAMENT for e in events) else ''} "
            f"options this week — all for adults 18+ 💪\n\n"
            f"✅ = Verified  ⚠️ = Community-reported\n\n"
            f"💬 DM us with your city + level for personalized picks!"
        )

        return IgCarousel(title=f"{city_label} Intel Drop", slides=slides,
                          caption=caption, hashtags=list(set(tags)))

    def skill_tip_carousel(self, skill: str, tips: List[dict]) -> IgCarousel:
        """
        Build a 5–7 slide skills breakdown carousel.
        tips = [{"headline": str, "body": str, "drill": optional str}]
        """
        slides = []
        skill_title = skill.title()

        # Slide 1: Hook
        slides.append(CarouselSlide(
            slide_number=1,
            headline=f"Level Up Your {skill_title}",
            body_lines=[
                "5 tips most players miss 🎯",
                "Try tip #3 at your next practice",
                "Swipe to level up ▶",
            ],
            is_cover=True,
        ))

        # Content slides
        for i, tip in enumerate(tips[:5], start=2):
            body = [tip["body"]]
            if tip.get("drill"):
                body.append(f"📋 Drill: {tip['drill']}")
            slides.append(CarouselSlide(
                slide_number=i,
                headline=f"Tip #{i-1}: {tip['headline']}",
                body_lines=body,
                emoji_accent="💡",
            ))

        # Final CTA slide
        slides.append(CarouselSlide(
            slide_number=len(slides) + 1,
            headline="Practice Makes Perfect",
            body_lines=[
                "Pick ONE tip. Drill it for 2 weeks.",
                "DM us your progress 🏐",
                "Follow for weekly skill drops",
            ],
            cta="Save this post for your next practice",
        ))

        caption = (
            f"🏐 {skill_title} breaking down your game? "
            f"These {len(tips)} tips will fix that FAST — swipe through and "
            f"try the drill on tip #3 tonight.\n\n"
            f"💬 Tag a teammate who needs to see this!\n"
            f"📌 Save this for your next practice session."
        )

        tags = self.CORE_HASHTAGS + [
            "#VolleyballTips", "#VolleyballSkills", f"#{skill_title}Training",
            "#VolleyballDrills", "#VolleyballCoach", "#VolleyballTraining",
        ]

        return IgCarousel(title=f"{skill_title} Tips", slides=slides,
                          caption=caption, hashtags=list(set(tags)))

    # ---------- Caption Builder ----------

    def single_event_caption(self, event: VolleyEvent) -> str:
        """
        Build a standalone caption for promoting a single event.
        Follows the HOOK → BODY → SOCIAL PROOF → CTA arc.
        """
        status = "✅ Verified Intel" if event.verified else "⚠️ Community-Reported"
        event_type_labels = {
            VolleyEventType.OPEN_GYM:   "Open Gym Alert 🏐",
            VolleyEventType.TOURNAMENT: "Tournament Alert 🏆",
            VolleyEventType.LEAGUE:     "League Registration Open 📋",
            VolleyEventType.CLINIC:     "Clinic Alert 🎯",
            VolleyEventType.BEACH:      "Beach Volleyball 🏖",
        }
        hook = event_type_labels.get(event.event_type, "Volleyball Intel 🏐")
        level = event.skill_level.value.replace("_", " ").title()

        lines = [
            f"🏐 {hook}",
            "",
            f"📌 **{event.name}**",
            f"📍 {event.venue_name}, {event.city}",
        ]

        if event.day_of_week and event.start_time:
            time_str = f"{event.day_of_week} @ {event.start_time}"
            if event.end_time:
                time_str += f" – {event.end_time}"
            lines.append(f"📅 {time_str}")
        elif event.start_date:
            lines.append(f"📅 {event.start_date}")

        lines.append(f"🎯 {level} | {event.gender.title()}")
        lines.append(f"💰 {event.cost or 'Contact organizer for pricing'}")

        if event.is_recurring:
            lines.append("🔄 Recurring — set a reminder!")

        if event.notes:
            lines.append(f"\n💬 {event.notes}")

        lines.append(f"\n{status}")

        if event.registration_url:
            lines.append(f"🔗 Register: {event.registration_url}")
        else:
            lines.append("💬 DM us for registration details!")

        if not event.verified:
            lines.append("\n_Details are community-reported. Always confirm directly with the organizer._")

        # Hashtags
        city_tags = self.LOCATION_HASHTAGS.get(event.city, [])
        event_tags = self.EVENT_HASHTAGS.get(event.event_type.value, [])
        all_tags = list(set(self.CORE_HASHTAGS[:6] + city_tags + event_tags))

        lines.append("\n" + " ".join(all_tags))
        return "\n".join(lines)

    # ---------- Reels Script Builder ----------

    def open_gym_reels_script(self, city: str, events: List[VolleyEvent]) -> ReelsScript:
        """
        Build a 30–45 second Reels script announcing open gym options.
        Reels format: fast cuts, direct address, visual cues.
        """
        count = len(events)
        top_event = events[0] if events else None

        sections = [
            {
                "label": "Context — 3-8s",
                "script": (f"If you're looking for volleyball in {city} this week, "
                           f"I've got {count} verified spot{'s' if count != 1 else ''} for you right now."),
                "visual": "Quick cuts of volleyball gameplay, b-roll of gym interiors",
            },
            {
                "label": "Value Delivery — 8-35s",
                "script": (f"Number one: {top_event.name if top_event else 'Open gym options'} "
                           f"at {top_event.venue_name if top_event else 'multiple venues'} — "
                           f"{top_event.day_of_week if top_event else 'weekly'} nights. "
                           f"Cost is {top_event.cost if top_event else 'varies by venue'}. "
                           f"Swipe up or check the caption for the full list."),
                "visual": "Text overlays: venue name, time, cost. Show map pin for location.",
            },
            {
                "label": "Credibility — 35-42s",
                "script": "We verify everything before we post it. If it says verified, it's real.",
                "visual": "Show ✅ checkmark animation",
            },
        ]

        return ReelsScript(
            title=f"{city} Open Gym Roundup",
            hook_line=f"3 volleyball open gyms in {city} this week — are you going?",
            sections=sections,
            cta_line=f"Follow @TheDailyDig for weekly {city} volleyball intel. Drop your questions below 👇",
            estimated_duration_sec=45,
        )
