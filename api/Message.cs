using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace api
{
    public enum Role
    {
        System,
        Assistant,
        User
    }

    public class Message
    {
        [JsonPropertyName("role")]
        public Role Role { get; set; }

        [JsonPropertyName("content")]
        public string Content { get; set; }
    }

    public class Root
    {
        [JsonPropertyName("messages")]
        public List<Message> Messages { get; set; }
    }

}
