from datetime import timedelta
from src.simulation.mixed_simulation import MixedClientSimulation
from src.simulation.client_types import ClientType, ClientConfig


def main():
    config = {
        ClientType.REAL_USER: ClientConfig(
            client_type=ClientType.REAL_USER, count=2, base_port=5000
        ),
        ClientType.SIMULATED: ClientConfig(client_type=ClientType.SIMULATED, count=5),
        ClientType.VIRTUAL_SOCKET: ClientConfig(
            client_type=ClientType.VIRTUAL_SOCKET, count=3, base_port=5000
        ),
    }

    simulation = MixedClientSimulation(config)

    try:
        simulation.setup_clients()
        simulation.run_simulation(duration=timedelta(hours=24))
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    finally:
        simulation.cleanup()


if __name__ == "__main__":
    main()
