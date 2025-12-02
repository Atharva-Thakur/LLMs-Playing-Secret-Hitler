"""
Display utilities for pretty console output
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from typing import List, Dict, Any


console = Console()


def print_header(text: str):
    """Print formatted header"""
    console.print(f"\n[bold cyan]{text}[/bold cyan]")
    console.print("=" * 80)


def print_game_state(state: Dict[str, Any]):
    """Print current game state"""
    table = Table(title="Game State")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Round", str(state.get('round', 'N/A')))
    table.add_row("Liberal Policies", f"{state.get('liberal_policies', 0)}/5")
    table.add_row("Fascist Policies", f"{state.get('fascist_policies', 0)}/6")
    table.add_row("Election Tracker", f"{state.get('election_tracker', 0)}/3")
    table.add_row("Phase", state.get('phase', 'N/A'))
    
    console.print(table)


def print_player_action(player_name: str, action: str, details: str = ""):
    """Print player action"""
    text = Text()
    text.append(f"[{player_name}] ", style="bold yellow")
    text.append(action, style="white")
    if details:
        text.append(f"\n  → {details}", style="dim")
    
    console.print(text)


def print_conversation(speaker: str, message: str):
    """Print conversation message"""
    panel = Panel(
        message,
        title=f"[bold]{speaker}[/bold]",
        border_style="blue",
        padding=(0, 1)
    )
    console.print(panel)


def print_decision(player_name: str, decision_type: str, decision: Any, reasoning: str):
    """Print player decision"""
    console.print(f"\n[bold yellow]{player_name}[/bold yellow] - {decision_type}")
    console.print(f"[green]Decision:[/green] {decision}")
    console.print(f"[dim]Reasoning:[/dim] {reasoning[:200]}...")


def print_game_over(winner: str, details: str):
    """Print game over message"""
    panel = Panel(
        f"[bold]{winner.upper()} WIN![/bold]\n\n{details}",
        title="🎮 GAME OVER 🎮",
        border_style="bold green" if winner.lower() == "liberal" else "bold red",
        padding=(1, 2)
    )
    console.print("\n")
    console.print(panel)


def print_error(message: str):
    """Print error message"""
    console.print(f"[bold red]ERROR:[/bold red] {message}")


def print_info(message: str):
    """Print info message"""
    console.print(f"[cyan]ℹ[/cyan] {message}")


def print_success(message: str):
    """Print success message"""
    console.print(f"[bold green]✓[/bold green] {message}")
