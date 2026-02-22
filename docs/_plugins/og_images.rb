# frozen_string_literal: true

module MillenniumDawn
  module OgImages
    module_function

    def seo_enabled?(doc)
      seo = doc.data["seo"]
      return true if seo.nil?
      return seo if seo.is_a?(TrueClass) || seo.is_a?(FalseClass)

      seo.to_s.strip.downcase != "false"
    end

    def explicit_image?(doc)
      doc.data.key?("image")
    end

    def slugify(value)
      cleaned = value.to_s.strip.downcase.gsub(/[^a-z0-9]+/, "-").gsub(/\A-+|-+\z/, "")
      cleaned.empty? ? "page" : cleaned
    end

    def og_id_for_rel_path(rel_path)
      stem = rel_path.to_s.sub(/\.[^\/.]+\z/, "")
      parts = stem.split("/").map { |part| slugify(part.sub(/\A_+/, "")) }
      parts.reject!(&:empty?)
      return "page" if parts.empty?

      parts.join("-")
    end

    def docs_rel_path(site, doc)
      rel =
        if doc.respond_to?(:relative_path) && !doc.relative_path.nil?
          doc.relative_path
        else
          path = doc.respond_to?(:path) ? doc.path : nil
          return nil if path.nil?

          source = site.source.to_s.gsub("\\", "/")
          path = path.to_s.gsub("\\", "/")
          path.sub(/\A#{Regexp.escape(source)}\/?/, "")
        end

      rel&.gsub("\\", "/")
    end

    def fallback_image(config, site_title)
      fallback = config.fetch("fallback", {})
      path = fallback["path"]
      return nil if path.nil? || path.to_s.strip.empty?

      {
        "path" => path.to_s,
        "width" => (fallback["width"] || 1200).to_i,
        "height" => (fallback["height"] || 630).to_i,
        "alt" => fallback["alt"] || site_title
      }
    end
  end
end

Jekyll::Hooks.register :site, :post_read do |site|
  og_config = site.config.fetch("og", {})
  generated_dir = og_config.fetch("generated_dir", "/assets/images/seo/generated").to_s
  generated_dir = generated_dir.sub(%r{\A/+}, "")
  site_title = site.config.fetch("title", "Millennium Dawn").to_s
  fallback = MillenniumDawn::OgImages.fallback_image(og_config, site_title)

  docs = site.collections.values.flat_map(&:docs)
  candidates = (site.pages + docs)

  candidates.each do |doc|
    next unless MillenniumDawn::OgImages.seo_enabled?(doc)
    next if MillenniumDawn::OgImages.explicit_image?(doc)

    rel_path = MillenniumDawn::OgImages.docs_rel_path(site, doc)
    next if rel_path.nil? || rel_path.empty?

    og_id = MillenniumDawn::OgImages.og_id_for_rel_path(rel_path)
    generated_rel = File.join(generated_dir, "#{og_id}.png").gsub("\\", "/")
    generated_abs = File.join(site.source, generated_rel)
    title = doc.data["title"] || site_title

    if File.exist?(generated_abs)
      doc.data["image"] = {
        "path" => "/#{generated_rel}",
        "width" => 1200,
        "height" => 630,
        "alt" => "Social preview for #{title}"
      }
    elsif fallback
      doc.data["image"] = fallback.dup
    end
  end
end
