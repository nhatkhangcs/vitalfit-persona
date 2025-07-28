import chainlit as cl
from enum import Enum
from pydantic import BaseModel, Field

# Định nghĩa các enum và mô hình Pydantic cho dữ liệu đầu vào
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class UserHealthInput(BaseModel):
    age: int = Field(..., ge=1, le=100,description="Age (years old)")
    gender: Gender = Field(..., description="Gender: male or female")
    weight: float = Field(..., ge=20, le=300, description="Weight (kg)")
    height: float = Field(..., ge=50, le=250, description="Height (cm)")


class HealthMetricsOutput(BaseModel):
    bmi: float = Field(..., description="BMI")
    bmi_category: str = Field(..., description="BMI category")
    body_fat_percentage: float = Field(..., description="Fat percentage %")


# Hàm tính toán chỉ số sức khỏe
def calculate_health_metrics(user_input: UserHealthInput) -> HealthMetricsOutput:
    # Tính BMI
    height_m = user_input.height / 100  # Chuyển cm sang m
    bmi = user_input.weight / (height_m ** 2)

    # Phân loại BMI
    if bmi < 18.5:
        bmi_category = "Underweight"
    elif 18.5 <= bmi < 25:
        bmi_category = "Normal"
    elif 25 <= bmi < 30:
        bmi_category = "Overweight"
    else:
        bmi_category = "Obese"

    # Tính Body Fat Percentage (Deurenberg)
    gender_value = 1 if user_input.gender == Gender.MALE else 0
    body_fat_percentage = (1.20 * bmi) + \
        (0.23 * user_input.age) - (10.8 * gender_value) - 5.4
    
    print("Calculating health metrics:")
    print("BMI:", round(bmi, 2))
    print("BMI Category:", bmi_category)
    print("Body Fat Percentage:", round(body_fat_percentage, 2))
    # display the logs to the UI

    return HealthMetricsOutput(
        bmi=round(bmi, 2),
        bmi_category=bmi_category,
        body_fat_percentage=round(
            max(0, body_fat_percentage), 2)  # Đảm bảo không âm
    )

# Asynchronous wrapper for the tool
def create_health_metric_tool():
    """
    Tool to calculate health metrics based on user input.
    
    Args:
        input (UserHealthInput): User's health data input.
    
    Returns:
        HealthMetricsOutput: Calculated health metrics.
    """
    @cl.step(type="tools")
    async def health_metric_tool(input: UserHealthInput) -> HealthMetricsOutput:
        return calculate_health_metrics(input)

    return health_metric_tool