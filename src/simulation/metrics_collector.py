from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class SimulationMetrics:
    start_time: datetime
    real_user_transactions: int = 0
    simulated_transactions: int = 0
    virtual_socket_transactions: int = 0
    failed_transactions: dict = None
    response_times: dict = None

    def to_json(self):
        return json.dumps(
            {
                "start_time": self.start_time.isoformat(),
                "real_user_transactions": self.real_user_transactions,
                "simulated_transactions": self.simulated_transactions,
                "virtual_socket_transactions": self.virtual_socket_transactions,
                "failed_transactions": self.failed_transactions,
                "response_times": self.response_times,
            },
            indent=2,
        )
