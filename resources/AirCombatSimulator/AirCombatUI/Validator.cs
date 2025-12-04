namespace AirCombatUI
{
    internal static class Validator
    {
        internal static double ValidateDouble(string text, string nameOfInput)
        {
            if (string.IsNullOrWhiteSpace(text))
            {
                throw new InvalidOperationException($"Could not parse {nameOfInput}");
            }

            if (double.TryParse(text, out double value))
            {
                return value;
            }

            throw new InvalidOperationException($"Could not parse {nameOfInput}");
        }

        internal static int ValidateInt(string text, string nameOfInput)
        {
            if (string.IsNullOrWhiteSpace(text))
            {
                throw new InvalidOperationException($"Could not parse {nameOfInput}");
            }

            if (int.TryParse(text, out int value))
            {
                return value;
            }

            throw new InvalidOperationException($"Could not parse {nameOfInput}");
        }

        internal static void ValidateRange(double var, double min, double max, string nameOfInput)
        {
            if (var < min || var > max)
            {
                throw new ArgumentOutOfRangeException(nameOfInput);
            }
        }
    }
}
