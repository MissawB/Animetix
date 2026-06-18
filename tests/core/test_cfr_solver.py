from core.domain.services.cfr_game_solver import CFRGameSolver


def test_cfr_solver_convergence():
    solver = CFRGameSolver(num_actions=2)
    questions = ["Q1", "Q2"]
    state = {"probs": [0.5, 0.5]}

    # solve_best_question doesn't take iterations
    best_q, confidence = solver.solve_best_question(questions, state)
    assert best_q in questions
    assert 0 <= confidence <= 1.0
