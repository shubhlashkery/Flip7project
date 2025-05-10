import random
from enum import Enum, auto
from typing import Optional, List, Dict, Any

class CardType(Enum):
    """
    Enumeration of all card types in Flip7.
    """
    NUMBER = auto()
    FLIP_THREE = auto()
    FREEZE = auto()
    SECOND_CHANCE = auto()
    ADDITIVE = auto()
    MULTIPLIER = auto()

class Card:
    """
    Abstract base class for cards in Flip7.
    """
    def __init__(self, card_type: CardType):
        self.card_type = card_type

class NumberCard(Card):
    """
    Represents a numbered card with a specific integer value.
    """
    def __init__(self, value: int):
        super().__init__(CardType.NUMBER)
        self.value = value

    def __repr__(self):
        return f"Number({self.value})"

class ActionCard(Card):
    """
    Represents an action card (Flip Three, Freeze, or Second Chance).
    """
    def __init__(self, action_type: CardType):
        if action_type not in (CardType.FLIP_THREE, CardType.FREEZE, CardType.SECOND_CHANCE):
            raise ValueError("Invalid action card type")
        super().__init__(action_type)

    def __repr__(self):
        return f"Action({self.card_type.name})"

class ModifierCard(Card):
    """
    Represents a modifier card that either adds to or multiplies the total.
    """
    def __init__(self, modifier_type: CardType, amount: int):
        if modifier_type not in (CardType.ADDITIVE, CardType.MULTIPLIER):
            raise ValueError("Invalid modifier card type")
        super().__init__(modifier_type)
        self.amount = amount

    def __repr__(self):
        return f"Modifier({self.card_type.name},{self.amount})"

class Deck:
    """
    Manages the draw and discard piles, auto-reshuffling when needed.
    """
    def __init__(self):
        self.cards: List[Card] = []
        self.discard: List[Card] = []
        counts = {i: i if i > 0 else 1 for i in range(13)}
        for value, cnt in counts.items():
            self.cards.extend(NumberCard(value) for _ in range(cnt))
        self.cards.extend(ActionCard(CardType.FLIP_THREE) for _ in range(4))
        self.cards.extend(ActionCard(CardType.FREEZE) for _ in range(4))
        self.cards.extend(ActionCard(CardType.SECOND_CHANCE) for _ in range(4))
        for add in [2,4,6,8,10]:
            self.cards.append(ModifierCard(CardType.ADDITIVE, add))
        self.cards.extend(ModifierCard(CardType.MULTIPLIER, 2) for _ in range(2))
        self.shuffle()

    def shuffle(self):
        """Shuffle draw pile."""
        random.shuffle(self.cards)

    def draw(self) -> Card:
        """Draw a card, auto-reshuffling if needed."""
        if not self.cards:
            if self.discard:
                self.cards, self.discard = self.discard, []
                self.shuffle()
            else:
                raise IndexError("Empty deck and discard")
        card = self.cards.pop()
        self.discard.append(card)
        return card

class PlayerState:
    """
    Tracks a player's round-specific state.
    """
    def __init__(self):
        self.flipped: List[NumberCard] = []
        self.modifiers: List[ModifierCard] = []
        self.has_second_chance: bool = False
        self.pending_flips: int = 0
        self.active: bool = True
        self.need_flip_decision: bool = False
        self.need_freeze_decision: bool = False
        self.busted: bool = False

    def reset_round(self):
        """Reset round state."""
        self.flipped.clear()
        self.modifiers.clear()
        self.has_second_chance = False
        self.pending_flips = 0
        self.active = True
        self.need_flip_decision = False
        self.need_freeze_decision = False
        self.busted = False

class GameState:
    """
    Main game environment for Flip7.
    """
    def __init__(self):
        self.deck = Deck()
        self.players: List[PlayerState] = [PlayerState(), PlayerState()]
        self.current: int = 0
        self.round_active: bool = True
        self.cumulative: List[int] = [0,0]

    def get_actions(self) -> List[str]:
        ps = self.players[self.current]
        if not ps.active or not self.round_active:
            return []
        if ps.need_flip_decision:
            return ['KeepFlipThree','PassFlipThree']
        if ps.need_freeze_decision:
            return ['KeepFreeze','PassFreeze']
        if ps.pending_flips>0:
            return ['Hit']
        return ['Hit','Stay']

    def compute_round_score(self, player: PlayerState) -> int:
        if player.busted:
            return 0
        total = sum(c.value for c in player.flipped)
        for m in player.modifiers:
            if m.card_type==CardType.MULTIPLIER:
                total*=m.amount
        for m in player.modifiers:
            if m.card_type==CardType.ADDITIVE:
                total+=m.amount
        if len({c.value for c in player.flipped})>=7:
            total+=15
        return total

    def step(self, action: str) -> Optional[Card]:
        ps = self.players[self.current]
        other = self.players[1-self.current]
        # Flip-three decision must be immediate, no turn toggle before decision.
        if ps.need_flip_decision and action in ('KeepFlipThree','PassFlipThree'):
            if action=='KeepFlipThree':
                ps.pending_flips+=3
                # current remains
            else:
                other.pending_flips+=3
                self.current=1-self.current
            ps.need_flip_decision=False
            return None
        # Freeze decision similarly immediate
        if ps.need_freeze_decision and action in ('KeepFreeze','PassFreeze'):
            if action=='KeepFreeze':
                pts=self.compute_round_score(ps)
                self.cumulative[self.current]+=pts
                ps.active=False
            else:
                pts=self.compute_round_score(other)
                self.cumulative[1-self.current]+=pts
                other.active=False
            ps.need_freeze_decision=False
            if any(p.active for p in self.players):
                self.current^=1
            else:
                self.round_active=False
            return None
        if not ps.active or not self.round_active:
            return None
        if action=='Stay':
            pts=self.compute_round_score(ps)
            self.cumulative[self.current]+=pts
            ps.active=False
            if any(p.active for p in self.players): self.current^=1
            else: self.round_active=False
            return None
        if action=='Hit':
            if ps.pending_flips>0: ps.pending_flips-=1
            card=self.deck.draw()
            if isinstance(card,NumberCard):
                if any(c.value==card.value for c in ps.flipped):
                    if not ps.has_second_chance:
                        ps.active=False; ps.busted=True
                    else:
                        ps.has_second_chance=False
                else:
                    ps.flipped.append(card)
            elif isinstance(card,ActionCard):
                if card.card_type==CardType.FLIP_THREE:
                    if other.active: ps.need_flip_decision=True
                    else : ps.pending_flips+=3
                elif card.card_type==CardType.FREEZE:
                    if other.active: ps.need_freeze_decision=True
                    else:
                        pts=self.compute_round_score(ps)
                        self.cumulative[self.current]+=pts; ps.active=False
                else: ps.has_second_chance=True
            else:
                ps.modifiers.append(card)
            # toggle after draw except if flip3 decision pending
            if not ps.need_flip_decision and not ps.need_freeze_decision and ps.pending_flips == 0:
                self.current^=1
            if not any(p.active for p in self.players): self.round_active=False
            return card
        return None

# --- Tests ----------------------------------------------
def _run_tests():
    gs=GameState()
    p=PlayerState(); p.flipped=[NumberCard(5),NumberCard(6)]; p.modifiers=[ModifierCard(CardType.MULTIPLIER,2),ModifierCard(CardType.ADDITIVE,3)]
    assert gs.compute_round_score(p)==25
    p2=PlayerState(); p2.flipped=[NumberCard(7)]; p2.busted=True
    assert gs.compute_round_score(p2)==0
    p3=PlayerState(); p3.flipped=[NumberCard(i) for i in range(7)]
    assert gs.compute_round_score(p3)==sum(range(7))+15
    print("All tests passed!")

if __name__=='__main__':
    _run_tests()

    
