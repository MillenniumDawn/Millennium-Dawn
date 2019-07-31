using System;
using System.Collections.Generic;
using System.Text;

namespace Validator.Structs
{
    public struct Ideology //Containes the name and ID of a country (This would be the main class if OOB)
    {
        public string name;
        public List<String> subIdeologies;
        public Ideology(String _name, List<String> _subIdeologies)
        {
            name = _name;
            subIdeologies = _subIdeologies;
        }
        public Ideology(String _name)
        {
            name = _name;
            subIdeologies = new List<string>();
        }
        public List<String> GetAllSuideologies ()
        {
            return subIdeologies;
        }

    }
}
