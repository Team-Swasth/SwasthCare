from django import forms

class DocumentUploadForm(forms.Form):
    document1 = forms.ImageField(label="Upload Document Image 1", required=False)
    document2 = forms.ImageField(label="Upload Document Image 2", required=False)
    document3 = forms.ImageField(label="Upload Document Image 3", required=False)
    document4 = forms.ImageField(label="Upload Document Image 4", required=False)

class EditExtractedDataForm(forms.Form):
    prod_name = forms.CharField(label="Product Name", max_length=255, required=False)
    prod_type = forms.CharField(label="Product Type", max_length=255, required=False)
    ingredients = forms.CharField(label="Ingredients", widget=forms.Textarea, required=False)
    allergen_info = forms.CharField(label="Allergen Info", widget=forms.Textarea, required=False)
    barcode = forms.CharField(label="Barcode", max_length=255, required=False)
    manufacturing_date = forms.DateField(
        label="Manufacturing Date",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    # Nutritional Info (split fields)
    energy_kcal = forms.FloatField(label="Energy (kcal)", required=False)
    protein_g = forms.FloatField(label="Protein (g)", required=False)
    total_fat_g = forms.FloatField(label="Total Fat (g)", required=False)
    saturated_fat_g = forms.FloatField(label="Saturated Fat (g)", required=False)
    trans_fat_g = forms.FloatField(label="Trans Fat (g)", required=False)
    cholesterol_mg = forms.FloatField(label="Cholesterol (mg)", required=False)
    carbohydrate_g = forms.FloatField(label="Carbohydrate (g)", required=False)
    sugars_g = forms.FloatField(label="Sugars (g)", required=False)
    fiber_g = forms.FloatField(label="Fiber (g)", required=False)
    sodium_mg = forms.FloatField(label="Sodium (mg)", required=False)
    calcium_mg = forms.FloatField(label="Calcium (mg)", required=False)
    iron_mg = forms.FloatField(label="Iron (mg)", required=False)
    potassium_mg = forms.FloatField(label="Potassium (mg)", required=False)
    vitamin_c_mg = forms.FloatField(label="Vitamin C (mg)", required=False)
    vitamin_d_mcg = forms.FloatField(label="Vitamin D (mcg)", required=False)
    expiry_tenure = forms.CharField(label="Expiry Tenure", max_length=255, required=False)
    expiry_date = forms.DateField(
        label="Expiry Date",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    special_diet = forms.MultipleChoiceField(
        label="Special Diet",
        required=False,
        choices=[
            ('halal', 'Halal'),
            ('kosher', 'Kosher'),
            ('vegan', 'Vegan'),
        ],
        widget=forms.CheckboxSelectMultiple
    )
    price = forms.FloatField(label="Price (₹)", required=False)

