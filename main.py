from dataclasses import dataclass
from drafter import *

set_website_title("Chem Calc")
set_site_information(
    author="Adam Haboussi",
    description="Used to Calculate Chem related things",
    sources="Thanks to the Drafter docs",
    planning=["Plan.pdf", "Design.pdf"],
    links=["https://github.com/Adam-Haboussi/Chem-Calc"]
)
hide_debug_information()
set_website_framed(False)

@dataclass
class Chemical:
    formula: str
    coefficient: int
    mass: float
    moles: float

@dataclass
class State:
    reaction: str
    chemicals: list[Chemical]
    actual_yield: float
    product: Chemical | None
    limiting_reactant: str
    theoretical_yield: float
    percent_yield: float
    message: str

ATOMIC_MASSES = {
    "H": 1.008, "O": 15.999, "C": 12.011, "N": 14.007,
    "Cl": 35.45, "Na": 22.990
}

def add_element(total: float, element: str, number: str) -> float:
    if element not in ATOMIC_MASSES:
        raise ValueError("Unknown element: " + element)
    count = int(number) if number else 1
    return total + ATOMIC_MASSES[element] * count

def get_molar_mass(formula: str) -> float:
    total_mass = 0.0
    element = ""
    number = ""

    for character in formula:
        if character.isupper():
            if element:
                total_mass = add_element(total_mass, element, number)
            element = character
            number = ""
        elif character.islower():
            element += character
        elif character.isdigit():
            number += character

    if element:
        total_mass = add_element(total_mass, element, number)

    return total_mass

def calculate_moles(chemical: Chemical) -> float:
    return chemical.mass / get_molar_mass(chemical.formula)

def update_moles(chemicals: list[Chemical]) -> None:
    for chemical in chemicals:
        chemical.moles = calculate_moles(chemical)

def find_limiting_reactant(chemicals: list[Chemical]) -> Chemical:
    limiting = chemicals[0]
    smallest_ratio = chemicals[0].moles / chemicals[0].coefficient

    for chemical in chemicals:
        ratio = chemical.moles / chemical.coefficient
        if ratio < smallest_ratio:
            smallest_ratio = ratio
            limiting = chemical

    return limiting

def calculate_theoretical_yield(limiting: Chemical, product: Chemical) -> float:
    product_moles = limiting.moles * product.coefficient / limiting.coefficient
    return product_moles * get_molar_mass(product.formula)

def calculate_percent_yield(actual: float, theoretical: float) -> float:
    if theoretical == 0:
        return 0
    return actual / theoretical * 100

def validate_input(mass: float) -> str:
    if mass <= 0:
        return "Mass must be positive."
    return ""

def parse_reactants(text: str) -> list[Chemical]:
    chemicals = []

    for line in text.splitlines():
        line = line.strip()
        if line == "":
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 3:
            raise ValueError("Each reactant needs: formula,coefficient,mass")

        formula = parts[0]
        coefficient = int(parts[1])
        mass = float(parts[2])

        if coefficient <= 0:
            raise ValueError("Coefficients must be positive.")
        error = validate_input(mass)
        if error:
            raise ValueError(error)

        chemicals.append(Chemical(formula, coefficient, mass, 0.0))

    if len(chemicals) == 0:
        raise ValueError("Please enter at least one reactant.")

    return chemicals

def find_product(reaction: str) -> Chemical:
    reaction = reaction.replace("→", "->")
    if "->" not in reaction:
        raise ValueError("Reaction must contain '->'.")

    # Use the first product listed (e.g. CO2 in "CO2 + 2H2O")
    products = reaction.split("->")[1].split("+")[0].strip()

    coefficient = 1
    formula = products
    number = ""

    for character in products:
        if character.isdigit():
            number += character
        else:
            break

    if number:
        coefficient = int(number)
        formula = products[len(number):].strip()

    return Chemical(formula, coefficient, 0.0, 0.0)

@route("/")
def home(state: State) -> Page:
    return Page(
        state,
        [
            Header("Chemistry Assistant"),
            Text("This tool helps students solve stoichiometry problems."),
            Span(
                Link("Start Calculation", "/calculate"),
                ", ",
                Link("Examples", "/examples"),
                ", ",
                Link("About", "/about"),
                ", ",
                Link("Formulas", "/formulas")
            )
        ]
    )

@route("/calculate")
def calculate(state: State) -> Page:
    content = [Header("Stoichiometry Calculator")]

    if state.message:
        content.append(Text("Error: " + state.message))

    content += [
        Text("Balanced Reaction (e.g. 2H2 + O2 -> 2H2O)"),
        TextBox("reaction", ""),
        Text("Reactants, one per line: formula,coefficient,mass"),
        TextArea("reactants", ""),
        Text("Actual Product Mass (g)"),
        TextBox("actual_yield", ""),
        Button("Calculate", submit_calculation)
    ]
    return Page(state, content)

@route
def submit_calculation(state: State, reaction: str, reactants: str, actual_yield: str) -> Page:
    try:
        actual = float(actual_yield)
        error = validate_input(actual)
        if error:
            raise ValueError(error)

        chemicals = parse_reactants(reactants)
        update_moles(chemicals)
        limiting = find_limiting_reactant(chemicals)
        product = find_product(reaction)
        theoretical = calculate_theoretical_yield(limiting, product)
        percent = calculate_percent_yield(actual, theoretical)
    except (ValueError, KeyError, IndexError) as e:
        state.message = str(e)
        return calculate(state)

    state.reaction = reaction
    state.chemicals = chemicals
    state.product = product
    state.actual_yield = actual
    state.limiting_reactant = limiting.formula
    state.theoretical_yield = theoretical
    state.percent_yield = percent
    state.message = ""

    return results(state)

@route("/results")
def results(state: State) -> Page:
    return Page(state, [
        Header("Results"),
        Text("Limiting Reactant: " + state.limiting_reactant),
        Text("Theoretical Yield: " + str(round(state.theoretical_yield, 3)) + " g"),
        Text("Percent Yield: " + str(round(state.percent_yield, 2)) + "%"),
        Link("New Calculation", "/clear")
    ])

@route("/examples")
def examples(state: State) -> Page:
    return Page(state, [
        Header("Examples"),
        Text("Water Formation: 2H2 + O2 -> 2H2O"),
        Text("Methane Combustion: CH4 + 2O2 -> CO2 + 2H2O"),
        Link("Home", "/")
    ])

@route("/formulas")
def formulas(state: State) -> Page:
    return Page(state, [
        Header("Formulas"),
        Text("Moles = grams / molar mass, "),
        Text("Percent Yield = Actual / Theoretical × 100 "),
        Link("Home", "/")
    ])

@route("/about")
def about(state: State) -> Page:
    return Page(state, [
        Header("About"),
        Text("Built using Python and Drafter. Can currently only use H, O, C, N, Cl, and Na."),
        Link("Home", "/")
    ])

@route("/clear")
def clear(state: State) -> Page:
    state.reaction = ""
    state.chemicals = []
    state.product = None
    state.actual_yield = 0
    state.limiting_reactant = ""
    state.theoretical_yield = 0
    state.percent_yield = 0
    state.message = ""
    return calculate(state)

if __name__ == "__main__":
    initial_state = State(
        reaction="",
        chemicals=[],
        product=None,
        actual_yield=0,
        limiting_reactant="",
        theoretical_yield=0,
        percent_yield=0,
        message=""
    )

    start_server(initial_state)
