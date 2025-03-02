import json

from .data import CAR_PACKAGES


class CarRentalService:
    """
          Car Rental Service.

          This class can also use a db or connect to external service.
          Json was used for videos purposes.

          Primary functions:

          - Save customer car issue reports

          - Save new customer rental

          - Process car rental payments

          - Process rental quotation
      """
    _instance = None
    FILE_PATH = "rentals.json"

    def __new__(cls):
        """
            Ensure only 1 instance of this class is created.
        """
        if cls._instance is None:
            cls._instance = super(CarRentalService, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance

    def _load_data(self):
        """Load existing data from JSON file, or initialize empty lists."""
        try:
            with open(self.FILE_PATH, "r") as f:
                data = json.load(f)
                self.rentals = data.get("rentals", [])
                self.issues = data.get("issues", [])
                self.enquiries = data.get("enquiries", [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.rentals = []
            self.issues = []
            self.enquiries = []

    def _save_data(self):
        """Save data to JSON file."""
        with open(self.FILE_PATH, "w") as f:
            f.write(json.dumps({
                "rentals": self.rentals,
                "issues": self.issues,
                "enquiries": self.enquiries
            }, indent=4))

    def packages(self):
        return CAR_PACKAGES

    def get_package_by_id(self, package_id: str) -> dict:
        for package in CAR_PACKAGES:
            if package.get("id") == package_id:
                return package

    def get_rental_duration(self):
        """system configured max allowed rental period in days."""
        return 30

    def save_rental_request(self, rental: dict):
        """Save a new car rental request."""
        self.rentals.append(rental)
        self._save_data()
        return rental

    def retrieve_user_rentals(self, mobile):
        """Retrieve all rentals for a user."""
        return [r for r in self.rentals if r["mobile"] == mobile]

    def save_rental_issue(self, mobile, issue):
        """Save an issue reported by a user."""
        issue_entry = {"mobile": mobile, "issue": issue}
        self.issues.append(issue_entry)
        self._save_data()
        return {"status": "Issue reported", "issue": issue}

    def save_user_enquiry(self, mobile, enquiry):
        """Save a user's enquiry."""
        enquiry_entry = {"mobile": mobile, "enquiry": enquiry}
        self.enquiries.append(enquiry_entry)
        self._save_data()
        return {"status": "Enquiry saved", "enquiry": enquiry}

    def calculate_rental_charges(self, rental_days: int, rate_per_day: float):
        """Calculate rental charges based on the number of days."""
        return rental_days * rate_per_day
