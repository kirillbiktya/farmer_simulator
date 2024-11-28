from setuptools import setup, find_packages

if __name__ == "__main__":  # install from pip
    dist = setup(
        name="farmer_simulator",
        version="1.0",
        author="kirillbiktya",
        author_email="16803695+kirillbiktya@users.noreply.github.com",
        description="Farmer simulator",
        url="https://github.com/kirillbiktya/farmer_simulator",
        packages=find_packages(),
        python_requires=">=3.12",
        script_args=['bdist_wheel']
    )