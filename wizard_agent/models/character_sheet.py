from pydantic import BaseModel, Field, computed_field


class AbilityScores(BaseModel):
    """The six core ability scores for a D&D character."""

    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def get_modifier(self, ability: str) -> int:
        """Calculate the modifier for a given ability score."""
        score = getattr(self, ability.lower())
        return (score - 10) // 2


class CharacterSheet(BaseModel):
    """A D&D 5e character sheet for a Level 1 Wizard."""

    # Progress tracking
    completed_steps: list[str] = Field(default_factory=list)

    # Basic info
    name: str | None = None
    race: str | None = None
    size: str | None = None
    speed: int = 30
    darkvision: int | None = None
    racial_traits: list[str] = Field(default_factory=list)

    # Ability scores
    ability_scores: AbilityScores = Field(default_factory=AbilityScores)
    background_ability_bonuses: dict[str, int] = Field(default_factory=dict)

    # Class info
    character_class: str | None = None
    level: int = 1
    hit_die: str | None = None
    max_hp: int | None = None

    # Proficiencies
    saving_throw_proficiencies: list[str] = Field(default_factory=list)
    skill_proficiencies: list[str] = Field(default_factory=list)
    weapon_proficiencies: list[str] = Field(default_factory=list)
    armor_proficiencies: list[str] = Field(default_factory=list)
    tool_proficiencies: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["Common"])

    # Background
    background: str | None = None
    background_feature: str | None = None
    origin_feat: str | None = None

    # Spellcasting
    spellcasting_ability: str | None = None
    spell_save_dc: int | None = None
    spell_attack_bonus: int | None = None
    spell_slots: dict[int, int] = Field(default_factory=dict)

    # Spells
    cantrips_known: list[str] = Field(default_factory=list)
    spellbook: list[str] = Field(default_factory=list)
    prepared_spells: list[str] = Field(default_factory=list)
    max_prepared_spells: int | None = None

    # Derived stats
    proficiency_bonus: int = 2
    armor_class: int | None = None
    initiative: int | None = None
    passive_perception: int | None = None

    @computed_field
    @property
    def total_ability_scores(self) -> dict[str, int]:
        """Calculate total ability scores including background bonuses (2024 rules)."""
        abilities = [
            "strength",
            "dexterity",
            "constitution",
            "intelligence",
            "wisdom",
            "charisma",
        ]
        totals = {}
        for ability in abilities:
            base = getattr(self.ability_scores, ability)
            background = self.background_ability_bonuses.get(ability, 0)
            totals[ability] = base + background
        return totals

    def get_total_modifier(self, ability: str) -> int:
        """Get the modifier for a total ability score (including bonuses)."""
        total = self.total_ability_scores[ability.lower()]
        return (total - 10) // 2
