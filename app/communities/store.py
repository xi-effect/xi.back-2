from collections import defaultdict

# TODO rethink user_id_to_sids structure for horizontal scaling
user_id_to_sids: dict[int, set[str]] = defaultdict(set)
