using System;
using System.Collections.Generic;
using System.Text;

namespace Validator.Structs
{
    public struct State //Containes the name and ID of a country (This would be the main class if OOB)
    {
        public string ID;
        public List<String> provinces;
        public State(String _ID, List<String> _provinces)
        {
            ID = _ID;
            provinces = _provinces;
        }
        public State(String _ID)
        {
            ID = _ID;
            provinces = new List<string>();
        }
        public List<String> GetAllStates()
        {
            return provinces;
        }

    }
}
