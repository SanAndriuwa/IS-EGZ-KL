"""Sukuria skaitinių ir kategorinių stulpelių paruošimą. Jo dar nemoko."""
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .data import CATEGORICAL, NUMERIC

def build_preprocessing(include_page_values=False):
    """Grąžina ColumnTransformer; medianos ir masteliai išmokstami tik fit metu."""
    # 1. Pasirenkame skaitinius stulpelius. Kopija nekeičia bendro NUMERIC sąrašo.
    numeric_columns = NUMERIC.copy()
    if include_page_values:
        numeric_columns.append('PageValues')

    # 2. Skaitinių duomenų apdorojimas vyksta dviem žingsniais.
    # Mediana užpildo tuščius langelius. Standartizavimas: (x - vidurkis) / nuokrypis.
    # Tai ypač naudinga logistinei regresijai, kai trukmės ir dažniai skirtingo masto.
    # Medžiams standartizavimas nėra būtinas, bet visiems paliekame tą pačią grandinę.
    numeric_steps = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])

    # 3. Kategorijos nėra dydžiai: Browser=4 nereiškia „dvigubai daugiau“ nei 2.
    # Tuščia kategorija pakeičiama dažniausia mokymo kategorija.
    # One-hot kiekvienai žinomai kategorijai sukuria atskirą 0/1 stulpelį.
    # Nežinoma kategorija nesukelia klaidos, bet jos poveikio modelis nėra išmokęs.
    category_steps = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])

    # 4. ColumnTransformer skirtingoms stulpelių grupėms pritaiko jų grandines
    # ir sujungia rezultatus į vieną skaitinę matricą.
    preprocessing = ColumnTransformer([
        ('numeric', numeric_steps, numeric_columns),
        ('category', category_steps, CATEGORICAL),
    ])

    return preprocessing
