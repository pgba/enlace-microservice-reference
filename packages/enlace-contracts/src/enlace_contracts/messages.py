from enlace_core.envelope import Envelope

from enlace_contracts.action import ActionResult
from enlace_contracts.curation import CuratedPayload
from enlace_contracts.retrieved import RetrievedPayload

RetrievedMessage = Envelope[RetrievedPayload]
CuratedMessage = Envelope[CuratedPayload]
ActionResultMessage = Envelope[ActionResult]
